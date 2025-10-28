const express = require("express");
const bodyParser = require("body-parser");
const request = require("request");
const apiai = require("apiai");

const app = express();

// Environment variables
const PAGE_ACCESS_TOKEN = process.env.PAGE_ACCESS_TOKEN || "your_page_token";
const CLIENT_ACCESS_TOKEN =
  process.env.CLIENT_ACCESS_TOKEN || "your_apiai_token";
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || "tuxedo_cat";

// Initialize API.AI
const apiaiApp = apiai(CLIENT_ACCESS_TOKEN);

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Start server
const server = app.listen(process.env.PORT || 5000, () => {
  console.log(
    "Express server listening on port %d in %s mode",
    server.address().port,
    app.settings.env,
  );
});

// Facebook Webhook Verification
app.get("/webhook", (req, res) => {
  // Fixed: hub.mode (was hub.mdoe)
  if (
    req.query["hub.mode"] === "subscribe" &&
    req.query["hub.verify_token"] === VERIFY_TOKEN
  ) {
    console.log("Validating webhook");
    res.status(200).send(req.query["hub.challenge"]);
  } else {
    console.error("Failed validation. Make sure the validation tokens match.");
    res.status(403).end();
  }
});

// Handle all messages
// Fixed: Added missing '/' in route
app.post("/webhook", (req, res) => {
  console.log("Webhook received:", req.body);

  if (req.body.object === "page") {
    req.body.entry.forEach((entry) => {
      entry.messaging.forEach((event) => {
        console.log("Event:", event);

        // Process message events
        if (event.message && event.message.text) {
          sendMessage(event);
        }
      });
    });
  }

  res.status(200).end();
});

// Send message function
function sendMessage(event) {
  let sender = event.sender.id;
  let text = event.message.text;

  // Send text to API.AI
  let apiai = apiaiApp.textRequest(text, {
    sessionId: "tabby_cat", // use any arbitrary id
  });

  apiai.on("response", (response) => {
    // Got a response from api.ai
    let aiText = response.result.fulfillment.speech;

    // Send response back to Facebook Messenger
    request(
      {
        // Fixed: facebook.com (was facebok.com)
        url: "https://graph.facebook.com/v2.6/me/messages",
        // Fixed: PAGE_ACCESS_TOKEN (was PAGE_ACCSESS_TOKEN)
        qs: { access_token: PAGE_ACCESS_TOKEN },
        method: "POST",
        json: {
          recipient: { id: sender },
          message: { text: aiText }, // Fixed: use aiText not original text
        },
      },
      function (error, response) {
        if (error) {
          console.log("Error sending message:", error);
        } else if (response.body.error) {
          console.log("Error:", response.body.error);
        } else {
          console.log("Message sent successfully!");
        }
      },
    );
  });

  apiai.on("error", (error) => {
    console.log("API.AI Error:", error);
  });

  apiai.end();
}
