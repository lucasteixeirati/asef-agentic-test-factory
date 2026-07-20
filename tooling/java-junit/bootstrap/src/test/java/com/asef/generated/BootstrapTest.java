package com.asef.generated;

import com.asef.fixture.Calculator;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

final class BootstrapTest {
    @Test void provesOfflineDependencies() { assertEquals(5, new Calculator().add(2, 3)); }
}
