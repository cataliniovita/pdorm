package lab;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.util.*;

public class Server {
    static Connection getConn() throws Exception {
        String host = Optional.ofNullable(System.getenv("DB_HOST")).orElse("db");
        String db = Optional.ofNullable(System.getenv("DB_NAME")).orElse("demo");
        String user = Optional.ofNullable(System.getenv("DB_USER")).orElse("app");
        String pass = Optional.ofNullable(System.getenv("DB_PASS")).orElse("apppass");
        String url = String.format("jdbc:mysql://%s:3306/%s?useUnicode=true&characterEncoding=utf8&useSSL=false", host, db);
        return DriverManager.getConnection(url, user, pass);
    }

    static Map<String, String> parseQuery(URI uri) {
        Map<String, String> q = new HashMap<>();
        String raw = uri.getRawQuery();
        if (raw == null) return q;
        for (String p : raw.split("&")) {
            String[] kv = p.split("=", 2);
            String k = URLDecoder.decode(kv[0], StandardCharsets.UTF_8);
            String v = kv.length > 1 ? URLDecoder.decode(kv[1], StandardCharsets.UTF_8) : "";
            q.put(k, v);
        }
        return q;
    }

    static void writeJson(HttpExchange ex, int status, String json) throws IOException {
        ex.getResponseHeaders().add("Content-Type", "application/json");
        byte[] b = json.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(status, b.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(b); }
    }

    static String jsonEscape(String s) { return s.replace("\\", "\\\\").replace("\"", "\\\""); }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", 8080), 0);

        server.createContext("/health", ex -> {
            try (Connection c = getConn()) {
                writeJson(ex, 200, "{\"ok\":true}");
            } catch (Exception e) {
                writeJson(ex, 500, "{\"ok\":false,\"error\":\"" + jsonEscape(e.getMessage()) + "\"}");
            }
        });

        server.createContext("/safe", ex -> {
            Map<String, String> q = parseQuery(ex.getRequestURI());
            String name = q.getOrDefault("name", "");
            String col = q.getOrDefault("col", "name");
            Set<String> allowed = new HashSet<>(Arrays.asList("id","name","color","price"));
            if (!allowed.contains(col)) { writeJson(ex, 400, "{\"error\":\"invalid column\"}"); return; }
            String sql = "SELECT `" + col + "` AS val FROM fruit WHERE name = ?";
            try (Connection c = getConn(); PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, name);
                ResultSet rs = ps.executeQuery();
                List<String> vals = new ArrayList<>();
                while (rs.next()) { vals.add(rs.getString("val")); }
                writeJson(ex, 200, "{\"rows\":" + vals.toString() + "}");
            } catch (Exception e) {
                writeJson(ex, 500, "{\"error\":\"" + jsonEscape(e.getMessage()) + "\"}");
            }
        });

        server.createContext("/vuln", ex -> {
            Map<String, String> q = parseQuery(ex.getRequestURI());
            String name = q.getOrDefault("name", "");
            String col = q.getOrDefault("col", "name");
            // VULN: manual identifier interpolation with naive backtick escaping
            String sanitized = col.replace("`", "``");
            String sql = "SELECT `" + sanitized + "` AS val FROM fruit WHERE name = ?";
            try (Connection c = getConn(); PreparedStatement ps = c.prepareStatement(sql)) {
                ps.setString(1, name);
                ResultSet rs = ps.executeQuery();
                List<String> vals = new ArrayList<>();
                while (rs.next()) { vals.add(rs.getString("val")); }
                writeJson(ex, 200, "{\"query\":\"" + jsonEscape(sql) + "\",\"rows\":" + vals.toString() + "}");
            } catch (Exception e) {
                writeJson(ex, 500, "{\"query\":\"" + jsonEscape(sql) + "\",\"error\":\"" + jsonEscape(e.getMessage()) + "\"}");
            }
        });

        server.start();
        System.out.println("java-jdbc listening on 8080");
    }
}


