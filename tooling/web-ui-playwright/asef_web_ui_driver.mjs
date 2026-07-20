import fs from "node:fs";
import net from "node:net";
import http from "node:http";
import process from "node:process";
import { isDeepStrictEqual } from "node:util";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { chromium } from "@playwright/test";

const require = createRequire(import.meta.url);
const playwrightVersion = require("@playwright/test/package.json").version;
const outputPath = "/asef-output/toolchain-result.json";
const executionOutputPath = "/asef-output/web-ui-result.json";
const fixtureRoot = "/workspace/fixture";
const allowedOrigin = "http://127.0.0.1:4173";

function printVersion() {
  process.stdout.write(JSON.stringify({
    schema_version: "1.0.0",
    node_version: process.versions.node,
    playwright_version: playwrightVersion,
  }) + "\n");
}

function writeIsBlocked(path) {
  try {
    fs.writeFileSync(path, "ASEF probe", { encoding: "utf8", flag: "wx" });
    fs.unlinkSync(path);
    return false;
  } catch {
    return true;
  }
}

function egressIsBlocked() {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "192.0.2.1", port: 80 });
    const finish = (blocked) => {
      socket.destroy();
      resolve(blocked);
    };
    socket.setTimeout(500, () => finish(true));
    socket.once("error", () => finish(true));
    socket.once("connect", () => finish(false));
  });
}

async function probe() {
  let browser;
  const result = {
    schema_version: "1.0.0",
    status: "ERROR",
    node_version: process.versions.node,
    playwright_version: playwrightVersion,
    chromium_version: null,
    uid: typeof process.getuid === "function" ? process.getuid() : null,
    gid: typeof process.getgid === "function" ? process.getgid() : null,
    headless: true,
    rootfs_read_only: writeIsBlocked("/var/tmp/asef-rootfs-probe"),
    workspace_read_only: writeIsBlocked("/workspace/.asef-write-probe"),
    egress_blocked: await egressIsBlocked(),
    diagnostic_code: null,
  };
  try {
    browser = await chromium.launch({
      headless: true,
      args: ["--disable-dev-shm-usage"],
    });
    result.chromium_version = browser.version();
    const context = await browser.newContext({
      acceptDownloads: false,
      serviceWorkers: "block",
    });
    const page = await context.newPage();
    await page.setContent("<!doctype html><title>ASEF probe</title><main>ready</main>");
    if (await page.title() !== "ASEF probe" || await page.locator("main").textContent() !== "ready") {
      throw new Error("browser probe content did not reconcile");
    }
    await context.close();
    const controlsPassed = result.uid !== 0
      && result.rootfs_read_only
      && result.workspace_read_only
      && result.egress_blocked;
    if (!controlsPassed) {
      throw new Error("container isolation probe failed");
    }
    result.status = "PASSED";
  } catch (error) {
    result.diagnostic_code = error instanceof Error && error.message === "container isolation probe failed"
      ? "ISOLATION_CONTROL_FAILED"
      : "BROWSER_START_FAILED";
  } finally {
    if (browser) {
      await browser.close();
    }
  }
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + "\n", "utf8");
  if (result.status !== "PASSED") {
    process.exitCode = 1;
  }
}

function locatorFor(page, locator) {
  if (locator.kind === "role") return page.getByRole(locator.value, { name: locator.name, exact: true });
  if (locator.kind === "label") return page.getByLabel(locator.value, { exact: true });
  return page.getByTestId(locator.value);
}

function fixtureServer() {
  const files = new Map([
    ["/", ["index.html", "text/html; charset=utf-8"]],
    ["/index.html", ["index.html", "text/html; charset=utf-8"]],
    ["/app.js", ["app.js", "text/javascript; charset=utf-8"]],
    ["/styles.css", ["styles.css", "text/css; charset=utf-8"]],
    ["/conformance.html", ["conformance.html", "text/html; charset=utf-8"]],
  ]);
  return http.createServer((request, response) => {
    const path = new URL(request.url, allowedOrigin).pathname;
    const entry = files.get(path);
    if (!entry || request.method !== "GET") {
      response.writeHead(404).end("not found");
      return;
    }
    response.writeHead(200, { "content-type": entry[1], "cache-control": "no-store" });
    response.end(fs.readFileSync(`${fixtureRoot}/${entry[0]}`));
  });
}

async function executeStep(page, step, timeout) {
  if (step.kind === "goto") return page.goto(`${allowedOrigin}${step.path}`, { waitUntil: "domcontentloaded", timeout });
  const locator = locatorFor(page, step.locator);
  if (step.kind === "click") return locator.click({ timeout });
  if (step.kind === "fill") return locator.fill(step.value, { timeout });
  if (step.kind === "check") return locator.check({ timeout });
  if (step.kind === "uncheck") return locator.uncheck({ timeout });
  throw new Error("POLICY:unknown action");
}

async function assertStep(page, step, timeout) {
  if (step.kind === "url") {
    if (new URL(page.url()).pathname !== step.expected) throw new Error("ASSERTION:url");
    return;
  }
  const locator = locatorFor(page, step.locator);
  await locator.waitFor({ state: "attached", timeout });
  let actual;
  if (step.kind === "visible") actual = await locator.isVisible();
  else if (step.kind === "text") actual = await locator.textContent();
  else if (step.kind === "value") actual = await locator.inputValue();
  else if (step.kind === "checked") actual = await locator.isChecked();
  else throw new Error("POLICY:unknown assertion");
  if (actual !== step.expected) throw new Error(`ASSERTION:${step.kind}`);
}

async function screenshot(page, scenarioId) {
  const ref = `screenshots/${scenarioId}.png`;
  try {
    await page.screenshot({ path: `/asef-output/${ref}`, type: "png", animations: "disabled" });
    return ref;
  } catch {
    return null;
  }
}

async function runScenario(browser, plan, scenario) {
  const started = Date.now();
  const context = await browser.newContext({
    viewport: { width: plan.viewport.width, height: plan.viewport.height },
    acceptDownloads: false,
    serviceWorkers: "block",
  });
  let policyViolation = null;
  const page = await context.newPage();
  context.on("page", (candidate) => { if (candidate !== page) policyViolation = "UNEXPECTED_PAGE"; });
  page.on("dialog", async (dialog) => { policyViolation = "DIALOG_BLOCKED"; await dialog.dismiss(); });
  page.on("download", (download) => { policyViolation = "DOWNLOAD_BLOCKED"; download.cancel().catch(() => {}); });
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== allowedOrigin) {
      policyViolation = "EXTERNAL_REQUEST_BLOCKED";
      await route.abort("blockedbyclient");
    } else {
      await route.continue();
    }
  });
  let failedStep = null;
  try {
    for (const action of scenario.actions) {
      failedStep = action.action_id;
      await executeStep(page, action, 3000);
      // Popup, download and route events can be delivered just after click resolves.
      // Drain that bounded browser event turn before accepting the action.
      if (action.kind === "click") await page.waitForTimeout(100);
      if (policyViolation) throw new Error(`POLICY:${policyViolation}`);
    }
    for (const assertion of scenario.assertions) {
      failedStep = assertion.assertion_id;
      await assertStep(page, assertion, 3000);
      if (policyViolation) throw new Error(`POLICY:${policyViolation}`);
    }
    await context.close();
    return { scenario_id: scenario.scenario_id, status: "PASSED", duration_ms: Date.now() - started,
      diagnostic_code: null, failed_step_id: null, screenshot_ref: null };
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown";
    const status = policyViolation || message.startsWith("POLICY:") ? "POLICY_BLOCKED"
      : message.startsWith("ASSERTION:") ? "FAILED"
      : error && error.name === "TimeoutError" ? "TIMEOUT" : "ERROR";
    const diagnostic = status === "POLICY_BLOCKED" ? (policyViolation || message.slice(7))
      : status === "FAILED" ? "ASSERTION_MISMATCH"
      : status === "TIMEOUT" ? "STEP_TIMEOUT" : "BROWSER_EXECUTION_ERROR";
    const screenshotRef = await screenshot(page, scenario.scenario_id);
    await context.close();
    return { scenario_id: scenario.scenario_id, status, duration_ms: Date.now() - started,
      diagnostic_code: diagnostic, failed_step_id: failedStep, screenshot_ref: screenshotRef };
  }
}

async function runPlan() {
  let browser;
  const server = fixtureServer();
  try {
    const planFile = JSON.parse(fs.readFileSync("/workspace/plan.json", "utf8"));
    const module = await import("file:///workspace/generated/web-ui-plan.ts");
    const plan = module.default;
    if (!isDeepStrictEqual(plan, planFile) || plan.base_url !== allowedOrigin) {
      throw new Error("compiled plan identity mismatch");
    }
    await new Promise((resolve, reject) => {
      server.once("error", reject);
      server.listen(4173, "127.0.0.1", resolve);
    });
    browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
    const scenarios = [];
    for (const scenario of plan.scenarios) scenarios.push(await runScenario(browser, plan, scenario));
    const count = (status) => scenarios.filter((item) => item.status === status).length;
    const result = {
      schema_version: "1.0.0", plan_id: plan.plan_id,
      status: count("POLICY_BLOCKED") ? "POLICY_BLOCKED" : count("ERROR") ? "ERROR"
        : count("TIMEOUT") ? "TIMEOUT" : count("FAILED") ? "FAILED" : "PASSED",
      tests: scenarios.length, passed: count("PASSED"), failed: count("FAILED"),
      errors: count("ERROR"), timeouts: count("TIMEOUT"), policy_blocked: count("POLICY_BLOCKED"), scenarios,
    };
    fs.writeFileSync(executionOutputPath, JSON.stringify(result, null, 2) + "\n", "utf8");
    if (result.status !== "PASSED") process.exitCode = 1;
  } catch {
    process.stderr.write("Web UI execution infrastructure error\n");
    process.exitCode = 2;
  } finally {
    if (browser) await browser.close();
    if (server.listening) await new Promise((resolve) => server.close(() => resolve()));
  }
}

function runUnitPlan() {
  const result = spawnSync(process.execPath, [
    "--test", "--test-reporter=tap", "/workspace/generated/asef-generated.test.ts",
  ], { encoding: "utf8", timeout: 30000, maxBuffer: 1024 * 1024 });
  fs.writeFileSync("/asef-output/node-unit.tap", result.stdout || "", "utf8");
  if (result.stderr) process.stderr.write(result.stderr);
  process.exitCode = result.error ? 2 : (result.status ?? 2);
}

const [command, ...extra] = process.argv.slice(2);
if (extra.length || !["version", "probe", "run", "unit-run"].includes(command)) {
  process.stderr.write("usage: asef_web_ui_driver.mjs version|probe|run|unit-run\n");
  process.exitCode = 2;
} else if (command === "version") {
  printVersion();
} else if (command === "probe") {
  await probe();
} else if (command === "run") {
  await runPlan();
} else {
  runUnitPlan();
}
