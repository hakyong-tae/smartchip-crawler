import express from "express";
import axios from "axios";
import * as cheerio from "cheerio";
import cors from "cors";

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

app.get("/api/smartchip-events", async (req, res) => {
  try {
    const response = await axios.get("https://smartchip.co.kr/main.html");
    const $ = cheerio.load(response.data);

    const events = [];

    $("select#usedata option").each((i, el) => {
      if (i >= 10) return false;
      const value = $(el).attr("value");
      const text = $(el).text().trim();
      events.push({ usedata: value, name: text });
    });

    res.json({ results: events });
  } catch (error) {
    console.error("Error fetching SmartChip events:", error);
    res.status(500).json({ error: "Failed to fetch events" });
  }
});

app.get("/api/smartchip-featured", async (req, res) => {
    try {
      const response = await axios.get("https://smartchip.co.kr/main.html");
      const $ = cheerio.load(response.data);
  
      const featured = [];
  
      $(".swiper-container.first .swiper-slide").each((i, el) => {
        const style = $(el).attr("style") || "";
        const onclick = $(el).attr("onclick") || "";
  
        const nameMatch = style.match(/images\/([\w\d가-힣_]+)_(포스터|poster)\.(jpg|png|webp)/);
        const usedataMatch = onclick.match(/usedata=(\d+)/);
  
        if (nameMatch && usedataMatch) {
          const name = nameMatch[1]; // e.g., "2025_커피빵빵"
          const usedata = usedataMatch[1]; // e.g., "202550000107"
          const url = `https://smartchip.co.kr/Search_Ballyno.html?usedata=${usedata}`;
          featured.push({ usedata, name, url });
        }
      });
  
      res.json({ results: featured });
    } catch (error) {
      console.error("Error fetching SmartChip featured events:", error);
      res.status(500).json({ error: "Failed to fetch featured events" });
    }
  });
  
  app.get("/api/runner/:eventId/:bibNo", async (req, res) => {
    const { eventId, bibNo } = req.params;
    const url = `https://smartchip.co.kr/return_data_livephoto.asp?nameorbibno=${bibNo}&usedata=${eventId}`;
  
    try {
      const response = await axios.get(url);
      const $ = cheerio.load(response.data);
  
      const firstRowText = $("table tr").first().text().replace(/\s+/g, " ").trim();
  
      const nameMatch = firstRowText.match(/^(\S+)\s/);
      const totalTimeMatch = firstRowText.match(/(\d{2}:\d{2}:\d{2})/);
      const speedMatch = firstRowText.match(/Speed\s+([\d.]+)\s+km\/h/);
  
      const name = nameMatch ? nameMatch[1] : null;
      const total_time = totalTimeMatch ? totalTimeMatch[1] : null;
      const speed = speedMatch ? `${speedMatch[1]} km/h` : null;
  
      const cleanText = (text) => text.replace(/\s+/g, " ").trim();
  
      const splits = [];
      $("table tr").slice(1).each((i, el) => {
        const tds = $(el).find("td");
        if (tds.length >= 3) {
          const point = cleanText($(tds[0]).text());
          const time = cleanText($(tds[1]).text());
          const pace = cleanText($(tds[2]).text());
          if (
            point &&
            time &&
            pace &&
            point !== "POINT" &&
            time !== "TIME" &&
            pace !== "TIME OF DAY"
          ) {
            splits.push({ point, time, pace });
          }
        }
      });
  
      res.json({
        name,
        bib: bibNo,
        eventId,
        total_time,
        speed,
        splits,
      });
    } catch (e) {
      console.error("Error fetching runner data:", e);
      res.status(500).json({ error: "기록 조회 실패" });
    }
  });
   
  

app.listen(PORT, () => {
  console.log(`✅ SmartChip proxy server running at http://localhost:${PORT}`);
});
