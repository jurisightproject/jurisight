const express = require("express");
const axios = require("axios");
const multer = require("multer");
const FormData = require("form-data");
const Chat = require("../models/chat");
const auth = require("../middleware/auth");

// const FLASK_BASE_URL = "http://localhost:5000";
const FLASK_BASE_URL = "https://jurisight-jurisight-ai.hf.space";

const chatbotRouter = express.Router();
const upload = multer();

chatbotRouter.post(
  "/summarize",
  auth,
  upload.single("file"),
  async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      const formData = new FormData();
      formData.append("file", req.file.buffer, {
        filename: req.file.originalname,
        contentType: req.file.mimetype,
      });

      const response = await axios.post(
        `${FLASK_BASE_URL}/summarize`,
        formData,
        {
          headers: {
            ...formData.getHeaders(),
            "x-auth-token": req.header("x-auth-token"),
          },
        }
      );

      const summaryText = response.data.summary;

      // Save summary to MongoDB
      await Chat.create({
        userId: req.user,
        message: "Summarize the uploaded document",
        response: summaryText,
        type: "summary",
      });

      res.json(response.data);
    } catch (e) {
      res
        .status(500)
        .json({ error: "Error communicating with summarization service" });
    }
  }
);

chatbotRouter.post("/chat", auth, async (req, res) => {
  try {
    const { message } = req.body;
    const flaskResponse = await axios.post(
      `${FLASK_BASE_URL}/chat`,
      { message },
      {
        headers: {
          "Content-Type": "application/json",
          "x-auth-token": req.header("x-auth-token"),
        },
      }
    );

    const responseText = flaskResponse.data.response;

    // Save chat to MongoDB
    await Chat.create({
      userId: req.user,
      message,
      response: responseText,
      type: "general",
    });

    res.json({ response: responseText });
  } catch (error) {
    res.status(500).json({ error: "Failed to fetch response from Flask API." });
  }
});

chatbotRouter.get("/chat-history", auth, async (req, res) => {
  try {
    const chatHistory = await Chat.find({ userId: req.user }).sort({
      timestamp: 1,
    });
    res.json(chatHistory);
  } catch (e) {
    res.status(500).json({ error: "Error fetching chat history" });
  }
});

chatbotRouter.delete("/delete-chat-history", auth, async (req, res) => {
  try {
    await Chat.deleteMany({ userId: req.user });
    res.json({ message: "Chat history deleted successfully" });
  } catch (e) {
    res.status(500).json({ error: "Error deleting chat history" });
  }
});

chatbotRouter.post("/retrieve-cases", auth, async (req, res) => {
  try {
    const { top_k } = req.body;
    const response = await axios.post(
      `${FLASK_BASE_URL}/retrieve-cases`,
      req.body,
      {
        headers: {
          "Content-Type": "application/json",
          "x-auth-token": req.header("x-auth-token"),
        },
      }
    );
    const caseLinks = response.data.case_links
      .map((item) => item.url)
      .join(", ");

    // Save retrieval to MongoDB
    await Chat.create({
      userId: req.user,
      message: `Retrieve top ${top_k} similar cases`,
      response: caseLinks,
      type: "retrieval",
    });

    res.json(response.data);
  } catch (e) {
    res
      .status(500)
      .json({
        error:
          "Error communicating with case retrieval service. Please upload a pdf before retrieval",
      });
  }
});

chatbotRouter.get("/fetch-form-data", async (req, res) => {
  try {
    const token = req.header("x-auth-token");
    const userId = req.user;
    const response = await axios.get(`${FLASK_BASE_URL}/fetch-form-data`, {
      headers: {
          "x-auth-token": token,
          "user-id": userId // Send user ID to Flask
      },
  });
  res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: "Error fetching form data from Flask" });
  }
});

module.exports = chatbotRouter;
