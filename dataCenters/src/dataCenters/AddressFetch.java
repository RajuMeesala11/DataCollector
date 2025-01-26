package dataCenters;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class AddressFetch {

	public static void main(String[] args) throws InterruptedException {
		// TODO Auto-generated method stub
		System.setProperty("webdriver.chrome.driver","/Users/raj/Documents/AutoTest/chromedriver-mac-x64/chromedriver");
		  
		WebDriver driver = new ChromeDriver();
		
		driver.get("https://www.datacenters.com/locations?query=USA");
		Thread.sleep(5000);
		
		
				

	}

}
