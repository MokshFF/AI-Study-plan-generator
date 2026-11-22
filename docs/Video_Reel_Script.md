# 🎥 90–150 Second Video Demonstration Reel Script

**Project Title**: AI-Powered Personalized Study Plan Generator Using Prompt Engineering  
**Problem ID**: C20  
**Target Duration**: 120 seconds (2 minutes)  
**Presenter(s)**: `[Student 1 / Student 2 / Student 3]`  
**Screen Setup**: Fullscreen browser showing Streamlit application at `http://localhost:8501`. Terminal window visible on secondary screen or split pane showing Ollama daemon.

---

## Storyboard & Timing Breakdown

```
[0:00 - 0:20] ──► [0:20 - 0:45] ──► [0:45 - 1:15] ──► [1:15 - 1:40] ──► [1:40 - 2:00]
Problem & Architecture   Form & Sample Load   Ollama & Prompt V3   Validator & CSV   Summary & Viva Takeaway
```

---

## Scene-by-Scene Script

### Scene 1: Introduction & Problem Context (0:00 – 0:20)
- **Visual**: Camera on presenter introducing the title card, transitioning to the clean Streamlit UI displaying *"Problem ID: C20 - AI-Powered Personalized Study Plan Generator"*.
- **Voiceover**:
  > *"Hello everyone! For our Prompt Engineering mini-project, we solved Problem C20: an AI-Powered Study Plan Generator for university students preparing for multi-subject exams.*  
  > *Most generative AI tools hallucinate study sessions after exams have ended or assign work on rest days. Our solution pairs local open-source LLMs running privately on Ollama with an independent Python verification engine to guarantee 100% schedule feasibility."*

---

### Scene 2: Interactive Form & Fictional Dataset (0:20 – 0:45)
- **Visual**: Presenter clicks the **"Load sample (DSA, DBMS, OS, NLP)"** button in the Streamlit UI. Form auto-populates with dates Dec 1–14, 4 subjects, exam dates, daily budget of 180 min, and overrides (Dec 6 set to 0 minutes for rest day).
- **Voiceover**:
  > *"Let's test it with a realistic scenario. Clicking 'Load sample' populates a 14-day exam window with four computer science subjects: DSA, DBMS, Operating Systems, and NLP.*  
  > *Notice that Dec 6 is marked as a 0-minute rest day right after the DSA exam, and DSA and OS are designated as weak subjects with specific topics like Dynamic Programming and Virtual Memory."*

---

### Scene 3: Prompt Engineering & Live Local Ollama Generation (0:45 – 1:15)
- **Visual**: Presenter points to the sidebar showing **Ollama Status: Connected**, Model: `qwen2.5:1.5b`. Presenter clicks **"🚀 Generate timetable"**. A progress spinner appears, showing live latency counter. Once completed (~75s or showing fast fixture), the timetable renders.
- **Voiceover**:
  > *"In the sidebar, we are connected to our local Ollama server running `qwen2.5:1.5b`. No cloud APIs or external keys are used—all student data stays 100% private on the laptop.*  
  > *Under the hood, our Prompt Engineering journey evolved through three versions:*  
  > *V1 was a naive zero-shot prompt that broke the JSON schema.*  
  > *V2 added few-shot formatting but hallucinated sessions after exam dates.*  
  > *Our final V3 uses 'Context Grounding'—it pre-calculates eligible subjects per day and enforces strict negative guardrails."*

---

### Scene 4: Independent Python Validation & Grouped Timetable (1:15 – 1:40)
- **Visual**: Camera zooms into the green banner: *"Plan Validated Successfully (0 errors)"*. Presenter scrolls through the day-by-day timetable cards:
  - Showing Dec 5 (DSA exam day with morning formula revision).
  - Showing Dec 6 (Rest Day: 0 minutes, empty session list).
  - Showing Dec 12–14 (Only NLP scheduled, DSA/DBMS/OS are completely absent).
  - Presenter clicks **"📥 Download Study Plan as CSV"** and opens the downloaded file.
- **Voiceover**:
  > *"Our pure Python validator independently checks 9 academic rules before anything is displayed.*  
  > *Look at the results: Dec 6 is strictly honored as a rest day with zero sessions. On Dec 5, our date-level rule permits quick pre-exam formula recall. And crucially, after Dec 5, no more DSA sessions are ever scheduled!*  
  > *Students can immediately export the valid timetable as a CSV spreadsheet."*

---

### Scene 5: Test Harness, Experiment Log & Conclusion (1:40 – 2:00)
- **Visual**: Presenter switches to the **"🧪 Experiment Logs & Prompts"** tab in Streamlit, showing the run history table and the 10/10 test matrix.
- **Voiceover**:
  > *"We verified the system against 10 distinct test cases—including reversed dates, budget overruns, and unknown subjects—all passing with 100% accuracy.*  
  > *Every run is tracked in our experiment log. This proves how thoughtful prompt engineering combined with deterministic validation transforms raw LLMs into reliable academic tools.*  
  > *Thank you!"*

---

## Recording Tips for the Team
1. **Pacing**: Speak at a clear, measured pace (~130 words per minute).
2. **Video Editing**: For the ~75-second Ollama generation wait, speed up that 5-second clip (4x) with a text overlay: *"Inference running locally on CPU (~75s)..."* to keep the total video runtime under 120 seconds.
3. **Audio Quality**: Use a lapel mic or headset microphone in a quiet room.
4. **Resolution**: Record in 1080p (1920x1080) at 30 or 60 fps.
