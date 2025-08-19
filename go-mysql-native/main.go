package main

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    _ "github.com/go-sql-driver/mysql"
)

type resp map[string]any

func jsonWrite(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    _ = json.NewEncoder(w).Encode(v)
}

func dsn(interpolate bool) string {
    host := env("DB_HOST", "db")
    user := env("DB_USER", "app")
    pass := env("DB_PASS", "apppass")
    name := env("DB_NAME", "demo")
    extra := "parseTime=true"
    if interpolate {
        extra += "&interpolateParams=true"
    }
    return fmt.Sprintf("%s:%s@tcp(%s:3306)/%s?%s", user, pass, host, name, extra)
}

func env(k, def string) string { if v := os.Getenv(k); v != "" { return v }; return def }

func main() {
    // Native prepares: interpolate=false
    db, err := sql.Open("mysql", dsn(false))
    if err != nil { log.Fatal(err) }
    if err := db.Ping(); err != nil { log.Fatal(err) }

    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        if err := db.Ping(); err != nil { jsonWrite(w, 500, resp{"ok": false, "error": err.Error()}); return }
        jsonWrite(w, 200, resp{"ok": true})
    })

    http.HandleFunc("/safe", func(w http.ResponseWriter, r *http.Request) {
        name := r.URL.Query().Get("name")
        col := r.URL.Query().Get("col")
        if col == "" { col = "name" }
        allowed := map[string]bool{"id": true, "name": true, "color": true, "price": true}
        if !allowed[col] { jsonWrite(w, 400, resp{"error": "invalid column"}); return }
        q := fmt.Sprintf("SELECT `%s` AS val FROM fruit WHERE name = ?", col)
        rows, err := db.Query(q, name)
        if err != nil { jsonWrite(w, 500, resp{"error": err.Error()}); return }
        var out []map[string]any
        for rows.Next() {
            var v sql.NullString
            if err := rows.Scan(&v); err != nil { continue }
            out = append(out, map[string]any{"val": v.String})
        }
        jsonWrite(w, 200, resp{"rows": out})
    })

    http.HandleFunc("/vuln", func(w http.ResponseWriter, r *http.Request) {
        name := r.URL.Query().Get("name")
        col := r.URL.Query().Get("col")
        if col == "" { col = "name" }
        // VULN: naive backtick escaping for identifiers
        sanitized := string([]rune(col))
        sanitized = string([]byte(fmt.Sprintf("%s", sanitized)))
        sanitized = replaceBackticks(sanitized)
        q := fmt.Sprintf("SELECT `%s` AS val FROM fruit WHERE name = ?", sanitized)
        rows, err := db.Query(q, name)
        if err != nil { jsonWrite(w, 500, resp{"query": q, "error": err.Error()}); return }
        var out []map[string]any
        for rows.Next() { var v sql.NullString; _ = rows.Scan(&v); out = append(out, map[string]any{"val": v.String}) }
        jsonWrite(w, 200, resp{"query": q, "rows": out})
    })

    log.Println("go-mysql-native listening on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}

func replaceBackticks(s string) string {
    out := make([]rune, 0, len(s))
    for _, r := range s { if r == '`' { out = append(out, '`', '`') } else { out = append(out, r) } }
    return string(out)
}


