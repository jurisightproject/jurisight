const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");
const bodyParser = require("body-parser");
const path = require("path");
const dotenv = require("dotenv");
const authRouter = require("./routes/auth");
const chatbotRouter = require("./routes/chatbot");

dotenv.config();
const PORT = process.env.PORT || 3000;
const app = express();
const DB = process.env.DB;

app.use(cors({ origin: "*" }));
app.use(express.json());
app.use(bodyParser.json());

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "login.html"));
});

app.use(express.static(path.join(__dirname, "public")));
app.use(authRouter);
app.use(chatbotRouter);

mongoose
  .connect(DB)
  .then(() => {
    console.log("Connection Successful");
  })
  .catch((e) => {
    console.log(e);
  });

app.listen(PORT, "0.0.0.0", async () => {
  console.log(`Connected at port ${PORT}`);
});
