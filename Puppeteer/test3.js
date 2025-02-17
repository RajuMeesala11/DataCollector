const fs = require('fs');

(async () => {
  // 1. Read the existing JSON file
  const rawData = fs.readFileSync('output_with_addresses.json', 'utf8');
  let data = JSON.parse(rawData);

  // 2. Loop through each state (or country)
  for (const state in data) {
    const details = data[state].details || [];
    
    // For each city in "details"
    for (let i = 0; i < details.length; i++) {
      const city = details[i];
      
      // If city.addresses is an array, process each site
      if (Array.isArray(city.addresses)) {
        city.addresses.forEach(site => {
          // If site.address exists, split by newline and create address1, address2, etc.
          if (site.address) {
            // Split on newline, trim whitespace, remove empty lines
            const lines = site.address.split('\n').map(line => line.trim()).filter(Boolean);
            
            // Assign each line to address1, address2, etc.
            lines.forEach((line, idx) => {
              site[`address${idx + 1}`] = line;
            });

            // Remove the original "address" property
            delete site.address;
          }
        });
      }
    }
  }

  // 3. Write the updated data to a new JSON file
  fs.writeFileSync('output_split_addresses.json', JSON.stringify(data, null, 2));
  console.log('Data saved to output_split_addresses.json with split address fields.');
})();