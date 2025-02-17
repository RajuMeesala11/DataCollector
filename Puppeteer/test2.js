const fs = require('fs');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const cliProgress = require('cli-progress');

// Use the stealth plugin
puppeteer.use(StealthPlugin());

// Helper function for a random delay between min and max milliseconds
function randomDelay(min = 1500, max = 3000) {
  const delayTime = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, delayTime));
}

(async () => {
  // Read the existing JSON file that already contains some address data
  const rawData = fs.readFileSync('output_with_addresses.json');
  let data = JSON.parse(rawData);

  // Build a list of tasks: only process cities whose "addresses" array is empty
  let tasks = [];
  for (const state in data) {
    const details = data[state].details;
    for (let i = 0; i < details.length; i++) {
      // Only add tasks if there's a URL and the addresses array is empty
      if (details[i].url && Array.isArray(details[i].addresses) && details[i].addresses.length === 0) {
        tasks.push({ state, index: i, city: details[i] });
      }
    }
  }

  console.log(`Found ${tasks.length} cities with empty addresses.`);

  // Set up a CLI progress bar for visual progress feedback
  const progressBar = new cliProgress.SingleBar({
    format: 'Processing |{bar}| {percentage}% || {value}/{total} cities',
    hideCursor: true,
    barCompleteChar: '\u2588',
    barIncompleteChar: '\u2591'
  });
  progressBar.start(tasks.length, 0);

  // Launch Puppeteer with stealth enabled
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Process each task (city with empty addresses)
  for (const task of tasks) {
    try {
      await page.goto(task.city.url, { waitUntil: 'networkidle2' });
      // Wait for the container that holds the address cards.
      // Adjust the timeout if needed.
      await page.waitForSelector('div.ui.centered.cards', { timeout: 10000 });
      
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
      
      // Update the data structure with the scraped addresses
      data[task.state].details[task.index].addresses = addresses;
    } catch (error) {
      console.error(`Error processing ${task.city.name} (${task.city.url}): ${error.message}`);
      // Leave the addresses array empty so you can try again later
      data[task.state].details[task.index].addresses = [];
    }
    
    progressBar.increment();
    await randomDelay(1500, 3000);
  }

  progressBar.stop();

  // Write the updated data back to the JSON file
  fs.writeFileSync('output_with_addresses.json', JSON.stringify(data, null, 2));
  await browser.close();
})();