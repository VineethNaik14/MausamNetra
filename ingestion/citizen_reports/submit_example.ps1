# Example of a REAL submission made by a person using the platform.
# Replace the values with the reporter's actual observation and GPS.
$body = @{
  text = "ENTER YOUR ACTUAL WEATHER OBSERVATION HERE"
  city = "Bengaluru"
  state = "Karnataka"
  latitude = 12.9716
  longitude = 77.5946
  event_type = "heavy_rain"
  media_url = $null
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8081/reports" -Method Post -ContentType "application/json" -Body $body
