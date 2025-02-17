const fs = require('fs');

(async () => {
  // 1. Read your existing JSON file
  const rawData = fs.readFileSync('output_with_addresses.json', 'utf8');
  let data = JSON.parse(rawData);

  // 2. For each state (or country) -> each city -> deduplicate 'addresses'
  for (const state in data) {
    const details = data[state].details || [];
    for (let i = 0; i < details.length; i++) {
      const city = details[i];
      if (Array.isArray(city.addresses)) {
        const uniqueAddresses = [];
        const seen = new Set();

        for (const site of city.addresses) {
          // Build a key based on the URL, or fall back to combining name + address
          const key = site.url
            ? site.url.trim().toLowerCase()
            : ((site.name || '') + '_' + (site.address || ''))
                .trim()
                .toLowerCase();

          // If we haven't seen this key yet, it's a new unique entry
          if (key && !seen.has(key)) {
            seen.add(key);
            uniqueAddresses.push(site);
          }
        }

        // Replace the old addresses array with the deduplicated array
        city.addresses = uniqueAddresses;
      }
    }
  }

  // 3. Write the updated data to a new JSON file
  fs.writeFileSync('output_with_unique_addresses.json', JSON.stringify(data, null, 2));
  console.log('Deduplicated data saved to output_with_unique_addresses.json');
})();