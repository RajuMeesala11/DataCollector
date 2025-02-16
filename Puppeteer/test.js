const fs = require('fs');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const cliProgress = require('cli-progress');

// Use the stealth plugin
puppeteer.use(StealthPlugin());

// Helper function for random delay between min and max milliseconds
function randomDelay(min = 1500, max = 3000) {
  return new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1)) + min));
}

(async () => {
  // Read the existing JSON file with initial data
  const rawData = fs.readFileSync('output.json');
  let data = JSON.parse(rawData);

  // Build a list of tasks: each city (inner detail) with a URL
  let tasks = [];
  for (const state in data) {
    const details = data[state].details;
    for (let i = 0; i < details.length; i++) {
      if (details[i].url) {
        tasks.push({ state, index: i, city: details[i] });
      }
    }
  }

  // Set up CLI progress bar
  const progressBar = new cliProgress.SingleBar({
    format: 'Processing |{bar}| {percentage}% || {value}/{total} cities',
    hideCursor: true,
    barCompleteChar: '\u2588',
    barIncompleteChar: '\u2591'
  });
  progressBar.start(tasks.length, 0);

  // Launch Puppeteer with stealth plugin active
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      // other args if needed
    ]
  });
  const page = await browser.newPage();

  // Loop over each city task
  for (const task of tasks) {
    try {
      await page.goto(task.city.url, { waitUntil: 'networkidle2' });
      // Wait for the cards container that holds the address cards; adjust selector as necessary
      await page.waitForSelector('div.ui.centered.cards', { timeout: 5000 });
      
      // Extract address cards with URL, name, and address details
      const addresses = await page.evaluate(() => {
        const cards = Array.from(document.querySelectorAll('div.ui.centered.cards a.ui.card'));
        return cards.map(card => {
          const url = card.href || null;
          const nameElem = card.querySelector('div.header');
          const descElem = card.querySelector('div.description');
          const name = nameElem ? nameElem.innerText.trim() : null;
          const address = descElem ? descElem.innerText.trim() : null;
          return { url, name, address };
        });
      });
      
      // Save the addresses under the corresponding city entry
      data[task.state].details[task.index].addresses = addresses;
    } catch (error) {
      // Output error only if it occurs for this task
      console.error(`Error processing ${task.city.name} (${task.city.url}): ${error.message}`);
      data[task.state].details[task.index].addresses = [];
    }
    
    progressBar.increment();
    // Use a random delay between 1.5 to 3 seconds to simulate human behavior
    await randomDelay(1500, 3000);
  }

  progressBar.stop();

  // Write the updated data to a new JSON file
  fs.writeFileSync('output_with_addresses.json', JSON.stringify(data, null, 2));
  await browser.close();
})();