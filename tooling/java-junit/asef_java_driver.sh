#!/usr/bin/env bash
set -u

command_name="${1:-}"
readonly maven_repo=/opt/asef-m2
readonly result_path=/asef-output/toolchain-result.json

write_probe() {
  local status="$1" rootfs="$2" workspace="$3" egress="$4" diagnostic="$5"
  printf '{"schema_version":"1.0.0","status":"%s","java_version":"21.0.11","maven_version":"3.9.16","junit_version":"5.13.4","surefire_version":"3.5.5","uid":%s,"gid":%s,"rootfs_read_only":%s,"workspace_read_only":%s,"egress_blocked":%s,"offline_cache_ready":true,"diagnostic_code":%s}\n' \
    "$status" "$(id -u)" "$(id -g)" "$rootfs" "$workspace" "$egress" "$diagnostic" > "$result_path"
}

case "$command_name" in
  version)
    printf 'java=21.0.11 maven=3.9.16 junit=5.13.4 surefire=3.5.5\n'
    ;;
  probe)
    rootfs=true; workspace=true; egress=true
    touch /asef-rootfs-probe 2>/dev/null && rootfs=false
    touch /workspace/.asef-write-probe 2>/dev/null && workspace=false
    timeout 2 bash -c 'exec 3<>/dev/tcp/1.1.1.1/443' 2>/dev/null && egress=false
    if [[ "$rootfs" == true && "$workspace" == true && "$egress" == true && "$(id -u)" != 0 ]]; then
      write_probe PASSED true true true null
    else
      write_probe ERROR "$rootfs" "$workspace" "$egress" '"ISOLATION_CONTROL_FAILED"'
      exit 20
    fi
    ;;
  run)
    mkdir -p /tmp/asef-home /tmp/project /asef-output/surefire
    cp -R /workspace/. /tmp/project/
    cd /tmp/project || exit 30
    mvn --offline --batch-mode --no-transfer-progress -Dmaven.repo.local="$maven_repo" test
    exit_code=$?
    if compgen -G 'target/surefire-reports/TEST-*.xml' >/dev/null; then
      cp target/surefire-reports/TEST-*.xml /asef-output/surefire/
    fi
    exit "$exit_code"
    ;;
  *)
    printf 'unsupported driver command\n' >&2
    exit 64
    ;;
esac
