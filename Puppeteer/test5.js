const fs = require('fs');

(async () => {
  // 1. Read your existing JSON file
  const rawData = fs.readFileSync('output_split_addresses.json', 'utf8');
  const data = JSON.parse(rawData);

  // We'll build a new object to hold the deduplicated results
  const newData = {};

  // 2. Loop through each state (or country)
  for (const state in data) {
    const oldStateObj = data[state];

    // Preserve the top-level fields (e.g., count)
    const newStateObj = {
      count: oldStateObj.count,
      details: []
    };

    // 3. For each city in the state's "details"
    for (const city of oldStateObj.details) {
      // Create a new city object with the same structure (except addresses, which we'll rebuild)
      const newCity = {
        name: city.name,
        url: city.url,
        count: city.count,
        addresses: []
      };

      // If "addresses" is an array, we'll process it
      if (Array.isArray(city.addresses)) {
        const seen = new Set(); // track unique address2 values

        for (const site of city.addresses) {
          // Remove the site if ANY property is null
          const hasNull = Object.values(site).some(val => val === null);
          if (hasNull) {
            continue; // skip this site
          }

          // We only consider sites that have a valid address2
          if (site.address2) {
            const key = site.address2.trim().toLowerCase();
            // Deduplicate based on address2
            if (!seen.has(key)) {
              seen.add(key);
              newCity.addresses.push(site);
            }
          }
        }
      }

      // Add the newCity object (with deduplicated addresses) to the state's details
      newStateObj.details.push(newCity);
    }

    // Store the processed state in newData
    newData[state] = newStateObj;
  }

  // 4. Write the updated data to a new JSON file
  fs.writeFileSync('unique_sites.json', JSON.stringify(newData, null, 2));
  console.log('Unique sites saved to unique_sites.json');
})();