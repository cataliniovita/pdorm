package lab;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.*;

@RestController
public class Controller {
    private final JdbcTemplate jdbc;

    public Controller(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @GetMapping("/health")
    public Map<String, Object> health() {
        jdbc.queryForList("SELECT 1");
        return Map.of("ok", true);
    }

    @GetMapping("/safe")
    public Map<String, Object> safe(@RequestParam(defaultValue = "") String name,
                                    @RequestParam(defaultValue = "name") String col) {
        Set<String> allowed = Set.of("id","name","color","price");
        if (!allowed.contains(col)) return Map.of("error","invalid column");
        String sql = "SELECT `" + col + "` AS val FROM fruit WHERE name = ?";
        List<Map<String,Object>> rows = jdbc.queryForList(sql, name);
        return Map.of("rows", rows);
    }

    @GetMapping("/vuln")
    public Map<String, Object> vuln(@RequestParam(defaultValue = "") String name,
                                    @RequestParam(defaultValue = "name") String col) {
        // VULN: naive backtick escaping for identifiers; interpolated before binding values
        String sanitized = col.replace("`", "``");
        String sql = "SELECT `" + sanitized + "` AS val FROM fruit WHERE name = ?";
        try {
            List<Map<String,Object>> rows = jdbc.queryForList(sql, name);
            return Map.of("query", sql, "rows", rows);
        } catch (Exception e) {
            return Map.of("query", sql, "error", e.getMessage());
        }
    }

    @GetMapping("/vuln-pg")
    public Map<String, Object> vulnPg(@RequestParam(defaultValue = "") String name,
                                      @RequestParam(defaultValue = "name") String col) {
        // VULN: naive double-quote escaping for Postgres identifiers
        String sanitized = col.replace("\"", "\"\"");
        String sql = "SELECT \"" + sanitized + "\" AS val FROM users WHERE name = ?";
        try {
            List<Map<String,Object>> rows = jdbc.queryForList(sql, name);
            return Map.of("query", sql, "rows", rows);
        } catch (Exception e) {
            return Map.of("query", sql, "error", e.getMessage());
        }
    }
}


