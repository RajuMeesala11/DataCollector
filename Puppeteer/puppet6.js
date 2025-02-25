const fs = require('fs');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const cliProgress = require('cli-progress');

// Use the stealth plugin
puppeteer.use(StealthPlugin());

// --- Proxy Credentials (Datacenter) ---
const PROXY_HOST = "dcp.evomi.com";
const PROXY_PORT = "2000";
const PROXY_USERNAME = "omsmart008";
const PROXY_PASSWORD = "dsilstuCbaicxePOdlHy";

// Construct the proxy server URL (without credentials)
const PROXY_SERVER = `http://${PROXY_HOST}:${PROXY_PORT}`;

// --- Filenames for progress ---
const INPUT_FILE = 'addresses.json';
const PROGRESS_FILE = 'addresses_with.json';

// Load existing progress if available; otherwise load the starting file.
let rawData;
if (fs.existsSync(PROGRESS_FILE)) {
  console.log(`Loading progress from ${PROGRESS_FILE}`);
  rawData = fs.readFileSync(PROGRESS_FILE, 'utf8');
} else {
  console.log(`No progress file found. Loading starting data from ${INPUT_FILE}`);
  rawData = fs.readFileSync(INPUT_FILE, 'utf8');
}
let data = JSON.parse(rawData);

// Build a list of tasks: for each site missing overviewHTML or specsHtml.
// A task is created if either field is missing, empty, or just "\n".
let tasks = [];
for (const state in data) {
  const details = data[state].details || [];
  details.forEach((city, cityIndex) => {
    if (Array.isArray(city.addresses)) {
      city.addresses.forEach((site, addressIndex) => {
        if (site.url) {
          const overviewMissing =
            !site.hasOwnProperty('overviewHTML') ||
            site.overviewHTML.trim() === "" ||
            site.overviewHTML.trim() === "\n";
          const specsMissing =
            !site.hasOwnProperty('specsHtml') ||
            site.specsHtml.trim() === "";
          if (overviewMissing || specsMissing) {
            tasks.push({
              state,
              cityIndex,
              addressIndex,
              url: site.url,
              overviewMissing,
              specsMissing,
            });
          }
        }
      });
    }
  });
}
console.log(`Found ${tasks.length} tasks to process.`);

// Set up a CLI progress bar.
const progressBar = new cliProgress.SingleBar({
  format: 'Processing |{bar}| {percentage}% || {value}/{total} tasks',
  hideCursor: true,
  barCompleteChar: '\u2588',
  barIncompleteChar: '\u2591'
});
progressBar.start(tasks.length, 0);

// Helper delay function.
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper: Check if an error is likely due to rate limiting.
function isRateLimitError(error) {
  const msg = error.message.toLowerCase();
  return msg.includes("rate") || msg.includes("limit");
}

// Process an overview task with retry logic.
async function processOverviewTask(task, browser, retries = 2) {
  const taskPage = await browser.newPage();
  try {
    await taskPage.authenticate({ username: PROXY_USERNAME, password: PROXY_PASSWORD });
    await taskPage.goto(task.url, { waitUntil: 'networkidle2', timeout: 30000 });
    await taskPage.authenticate({ username: PROXY_USERNAME, password: PROXY_PASSWORD });
    // Extract overview using XPath expressions.
    const overviewHTML = await taskPage.evaluate(() => {
      function getHTMLByXPath(xpath) {
        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        return result.singleNodeValue ? result.singleNodeValue.outerHTML : "";
      }
      const el1 = getHTMLByXPath("//h1[@class='customheader']/../div");
      const el2 = getHTMLByXPath("//a[text()='Overview']/../../../div[contains(@class,'container')]");
      return el1 + "\n" + el2;
    });
    if (overviewHTML.trim() === "" || overviewHTML.trim() === "\n") {
      console.log(`Overview HTML is empty for URL: ${task.url}`);
    } else {
      data[task.state].details[task.cityIndex].addresses[task.addressIndex].overviewHTML = overviewHTML;
      console.log(`Overview HTML saved for URL: ${task.url}`);
    }
  } catch (error) {
    console.error(`Error processing overview for URL: ${task.url} - ${error.message}`);
    // Save progress and terminate immediately.
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify(data, null, 2));
    await browser.close();
    process.exit(1);
  } finally {
    await taskPage.close();
  }
}

// Process a specs task with retry logic.
async function processSpecsTask(task, browser, retries = 2) {
  const taskPage = await browser.newPage();
  try {
    await taskPage.authenticate({ username: PROXY_USERNAME, password: PROXY_PASSWORD });
    await taskPage.goto(task.url, { waitUntil: 'networkidle2', timeout: 30000 });
    await delay(2000); // Extra wait for the page to load.
    await taskPage.authenticate({ username: PROXY_USERNAME, password: PROXY_PASSWORD });
    // Click the Specs tab.
    const specsLink = await taskPage.$("a.tablink[href*='/specs/']");
    if (!specsLink) {
      throw new Error(`Specs tab not found for URL: ${task.url}`);
    }
    await specsLink.click();
    await taskPage.waitForSelector('div.ui.stackable.grid', { timeout: 10000 });
    // Extract the two elements using XPath.
    const specsHtml = await taskPage.evaluate((xpath1, xpath2) => {
      function getHTMLByXPath(xpath) {
        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        return result.singleNodeValue ? result.singleNodeValue.outerHTML : "";
      }
      return getHTMLByXPath(xpath1) + "\n" + getHTMLByXPath(xpath2);
    }, "//div[contains(@class,'statistics')]", "//table[contains(@class,'basic')]/../..");
    data[task.state].details[task.cityIndex].addresses[task.addressIndex].specsHtml = specsHtml;
    console.log(`Specs HTML saved for URL: ${task.url}`);
  } catch (error) {
    console.error(`Error processing specs for URL: ${task.url} - ${error.message}`);
    if (retries > 0 && isRateLimitError(error)) {
      console.warn(`Rate limit detected for URL: ${task.url}. Retrying in 5000ms... (Retries left: ${retries})`);
      await delay(5000);
      await processSpecsTask(task, browser, retries - 1);
    } else {
      fs.writeFileSync(PROGRESS_FILE, JSON.stringify(data, null, 2));
      await browser.close();
      process.exit(1);
    }
  } finally {
    await taskPage.close();
  }
}

// Main processing (sequential execution for simplicity).
(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [`--proxy-server=${PROXY_SERVER}`, '--no-sandbox', '--disable-setuid-sandbox']
  });
  
  for (let i = 0; i < tasks.length; i++) {
    const task = tasks[i];
    if (task.overviewMissing) {
      await processOverviewTask(task, browser);
    }
    if (task.specsMissing) {
      await processSpecsTask(task, browser);
    }
    progressBar.increment();
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify(data, null, 2));
    await delay(Math.floor(Math.random() * 2000) + 1500);
  }
  
  progressBar.stop();
  console.log(`Progress saved to ${PROGRESS_FILE}`);
  await browser.close();
})();