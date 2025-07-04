# Better Relics
A tool for Elden Ring Nightreign to import and browse/search through your relics. This is not a mod to edit your game, but instead a supplimentary app to aid you in deciding which relics to pick from your collection.
TLDR:
To import your relics, record a screen capture of you (fullscreen) scrolling through the *Sell* screen in the *Relic Rites* menu by holding right on the D-pad to cycle through all your relics. Save the video as `relics.mp4` file (tested in 1920x1080 at 60fps). Then, launch the program and click the Update Relics button to select your `relics.mp4` and begin processing.
To import your relics, record a screen capture of you (fullscreen) scrolling through the *Sell* screen in the *Relic Rites* menu by holding right on the D-pad to cycle through all your relics. Save the video as `relics.mp4` file (tested in 1920x1080 at 60fps). Then, launch the program and click the Update Relics button to select your `relics.mp4` and begin processing.


---

## Getting Started

### Prerequisites
To import your relics
- Record a screen capture of you (fullscreen) scrolling through the *Sell* screen in the *Relic Rites* menu by holding right on the D-pad to cycle through all your relics. 
  - Save the video as `relics.mp4` (at `1920x1080`, `60fps`).
  - Save the video as `relics.mp4` (at `1920x1080`, `60fps`).

### Installing
Open a terminal, navigate to this folder and run:
```bash
pip -r requirements.txt
```
>*[Optional] recommended to start a virtual python env to install this in with:*
> ```bash
> python -m venv venv
> .\venv\Scripts\Activate.ps1   # Windows
> source ./venv/bin/activate    # MacOS
> ```

---
## Running the App
Launch the program with
```bash
python BetterRelics.py
```
- In the application opened, click the `Update Relics` button to select your `relics.mp4` recording.
- Select the desired colors drop the dropdown menu to begin browsing. 
Below the dropdown bar is a search bar.


---

## License & Attribution

*This project is not affiliated with, endorsed by, or sponsored by FromSoftware or Bandai Namco. All trademarks, game titles, logos, and in-game assets (including icons) are the property of their respective owners.*

*This project is a non-commercial fan-made tool designed to help Nightfarers. All game-related assets, including icons and names, are the property of FromSoftware and Bandai Namco, used here for clarity. Icons used in this project are extracted from **Elden Ring Nightreign** and are used here for educational and non-commercial purposes.*