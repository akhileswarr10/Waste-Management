# Generator logic

1. Generate natural waste at each hour using area type, hourly pattern,
   weekday/weekend, season, holidays/events, weather and bin multiplier.
2. Simulate actual collection events separately and reset the physical bin
   state for sensor/operational history.
3. Compute ML targets counterfactually from the current true fill plus the
   next 3/6/12/24 hours of natural generation ONLY.
4. Never subtract future collected waste from the ML target.
5. Keep collection history and collection logs for scheduling and routing.
