// Tiny structured logger. Every line is one JSON object with a timestamp,
// level, and event name — easy to read in Vercel/Railway logs and easy to
// search ("give me every line with event=driver_login_failed").
type Level = "info" | "warn" | "error";

function write(level: Level, event: string, details?: Record<string, unknown>) {
  const line = JSON.stringify({
    t: new Date().toISOString(),
    level,
    event,
    ...details,
  });
  if (level === "error") console.error(line);
  else if (level === "warn") console.warn(line);
  else console.log(line);
}

export const log = {
  info: (event: string, details?: Record<string, unknown>) => write("info", event, details),
  warn: (event: string, details?: Record<string, unknown>) => write("warn", event, details),
  error: (event: string, details?: Record<string, unknown>) => write("error", event, details),
};
