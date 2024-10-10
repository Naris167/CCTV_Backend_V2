// Function to format date without time zone
export function formatDate(date) {
    const dateObj = date instanceof Date ? date : new Date(date);
  
    const pad = (num) => (num < 10 ? '0' + num : num);
    
    const year = dateObj.getFullYear();
    const month = pad(dateObj.getMonth() + 1); // getMonth() is zero-indexed
    const day = pad(dateObj.getDate());
    const hours = pad(dateObj.getHours());
    const minutes = pad(dateObj.getMinutes());
    const seconds = pad(dateObj.getSeconds());
  
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}


export function calculateRuntime(startTime) {
    const now = Date.now();
    let runningTime = now - startTime;
  
    const units = [
      { divisor: 31536000000, name: "year" },   // milliseconds in a year
      { divisor: 2592000000, name: "month" },   // milliseconds in a 30-day month
      { divisor: 86400000, name: "day" },       // milliseconds in a day
      { divisor: 3600000, name: "hour" },       // milliseconds in an hour
      { divisor: 60000, name: "minute" },       // milliseconds in a minute
      { divisor: 1000, name: "second" }         // milliseconds in a second
    ];
  
    const parts = [];
  
    for (const { divisor, name } of units) {
      if (name === "month") {
        // Special handling for months due to variable length
        const monthsPassed = calculateMonths(startTime, now);
        if (monthsPassed > 0) {
          parts.push(`${monthsPassed} ${name}${monthsPassed > 1 ? 's' : ''}`);
          runningTime -= monthsPassed * divisor;
        }
      } else {
        const value = Math.floor(runningTime / divisor);
        if (value > 0) {
          parts.push(`${value} ${name}${value > 1 ? 's' : ''}`);
          runningTime %= divisor;
        }
      }
    }
  
    if (parts.length === 0) {
      return "less than a second";
    } else if (parts.length === 1) {
      return parts[0];
    } else {
      const lastPart = parts.pop();
      return `${parts.join(', ')} and ${lastPart}`;
    }
}

function calculateMonths(start, end) {
    const startDate = new Date(start);
    const endDate = new Date(end);
    let months = (endDate.getFullYear() - startDate.getFullYear()) * 12;
    months += endDate.getMonth() - startDate.getMonth();
    if (endDate.getDate() < startDate.getDate()) {
      months--;
    }
    return months;
}