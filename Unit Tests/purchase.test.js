// purchase.test.js
const { JSDOM } = require('jsdom');
const path = require('path');
const fs = require('fs');

// Path to your HTML and JS files
const htmlPath = path.join(__dirname, '..', 'templates', 'purchase.html');
const jsPath = path.join(__dirname, '..', 'static', 'purchase.js');

let dom;
let document;
let window;

beforeEach(() => {
    // Create a new JSDOM instance for each test
    const html = fs.readFileSync(htmlPath, 'utf8');
    dom = new JSDOM(html, { runScripts: 'dangerously' });
    window = dom.window;
    document = dom.window.document;

    // Add the script to the DOM and execute it
    const scriptElement = document.createElement('script');
    scriptElement.textContent = fs.readFileSync(jsPath, 'utf8');
    document.body.appendChild(scriptElement);

    // Mock global functions and variables
    global.localStorage = {
        getItem: jest.fn(key => {
            const data = {
                make: 'Mock Make',
                model: 'Mock Model',
                price: '25000',
                vehicleID: '123',
            };
            return data[key];
        }),
    };
    global.alert = jest.fn(); // Mock the alert function
});

afterEach(() => {
    jest.clearAllMocks(); // Clean up mocks after each test
});

describe('Purchase Confirmation Logic', () => {
    test('should show alert for missing required fields', async () => {
        // Simulate a click without filling in any fields
        const confirmButton = document.getElementById('confirmButton');
        confirmButton.click();

        // The validation should prevent the fetch call
        expect(global.alert).toHaveBeenCalledWith("⚠️ Please fill out all required fields before confirming your purchase.");
    });

    test('should show alert for invalid card number format', async () => {
        // Fill in valid data, but use a bad card number
        document.getElementById('address').value = '123 Test St';
        document.getElementById('city').value = 'Testville';
        document.getElementById('state').value = 'TS';
        document.getElementById('zip').value = '12345';
        document.getElementById('cardName').value = 'Test User';
        document.getElementById('cardNumber').value = '1234'; // Too short
        document.getElementById('expDate').value = '2025-10';
        document.getElementById('cvv').value = '123';
        document.querySelector('input[value="in-store"]').checked = true;

        const confirmButton = document.getElementById('confirmButton');
        confirmButton.click();

        expect(global.alert).toHaveBeenCalledWith("⚠️ Invalid card number. Please enter a 16-digit number.");
    });

    test('should show alert for failed Luhn check', async () => {
        // Fill in valid data, but use a card number that fails the Luhn check
        document.getElementById('address').value = '123 Test St';
        document.getElementById('city').value = 'Testville';
        document.getElementById('state').value = 'TS';
        document.getElementById('zip').value = '12345';
        document.getElementById('cardName').value = 'Test User';
        document.getElementById('cardNumber').value = '49927398716'; // Fails check
        document.getElementById('expDate').value = '2025-10';
        document.getElementById('cvv').value = '123';
        document.querySelector('input[value="in-store"]').checked = true;

        const confirmButton = document.getElementById('confirmButton');
        confirmButton.click();

        expect(global.alert).toHaveBeenCalledWith("⚠️ Invalid card number. Please a real card number.");
    });

    test('should show alert for name mismatch from database', async () => {
        // Mock the fetch API to simulate a database response
        global.fetch = jest.fn()
            .mockResolvedValueOnce({ // Mock /get-user-data
                json: () => Promise.resolve([{ first_name: 'Database', last_name: 'User' }]),
            })
            .mockResolvedValueOnce({ // Mock /save-purchase-info
                ok: true,
            });

        // Fill in data with a card name that doesn't match the mock database
        document.getElementById('address').value = '123 Test St';
        document.getElementById('city').value = 'Testville';
        document.getElementById('state').value = 'TS';
        document.getElementById('zip').value = '12345';
        document.getElementById('cardName').value = 'Invalid Name';
        document.getElementById('cardNumber').value = '4992739871650392'; // Valid Luhn
        document.getElementById('expDate').value = '2025-10';
        document.getElementById('cvv').value = '123';
        document.querySelector('input[value="in-store"]').checked = true;

        const confirmButton = document.getElementById('confirmButton');
        await confirmButton.click();

        expect(global.alert).toHaveBeenCalledWith("⚠️ Invalid name. Please your real name.");
    });

    test('should handle a successful in-store purchase', async () => {
        // Mock the fetch API for the two calls
        global.fetch = jest.fn()
            .mockResolvedValueOnce({ // Mock /get-user-data
                json: () => Promise.resolve([{ first_name: 'Test', last_name: 'User' }]),
            })
            .mockResolvedValueOnce({ // Mock /save-purchase-info
                ok: true,
            });

        // Stub Math.random() to make generatedCode predictable
        const mockRandom = jest.spyOn(Math, 'random').mockReturnValue(0.5);

        // Fill in valid data
        document.getElementById('address').value = '123 Test St';
        document.getElementById('city').value = 'Testville';
        document.getElementById('state').value = 'TS';
        document.getElementById('zip').value = '12345';
        document.getElementById('cardName').value = 'Test User';
        document.getElementById('cardNumber').value = '4992739871650392'; // A valid number
        document.getElementById('expDate').value = '2025-10';
        document.getElementById('cvv').value = '123';
        document.querySelector('input[value="in-store"]').checked = true;
        document.getElementById('saveInfo').checked = true;

        const confirmButton = document.getElementById('confirmButton');
        await confirmButton.click();

        expect(global.alert).toHaveBeenCalledWith(expect.stringContaining("✅ Purchase confirmed!"));
        expect(global.alert).toHaveBeenCalledWith(expect.stringContaining("ready for pickup in-store"));
        expect(global.alert).toHaveBeenCalledWith(expect.stringContaining("Your information has been saved"));
        expect(global.alert).toHaveBeenCalledWith(expect.stringContaining("pick-up code for your vehicle is: 5490"));
    });
});
