# Project Progress: Simple Video Library

| ID   | Feature Name                                   | Status    | Dependencies      |
|------|------------------------------------------------|-----------|-------------------|
| F001 | Main Application Window UI & Navigation        | Pending   |                   |
| F002 | Font Configuration                             | Completed |                   |
| F003 | Video Library Backend (Data & Core Functions)  | Completed |                   |
| F004 | Library Item Class Definition                  | Completed |                   |
|      | **Check Videos Module** |           |                   |
| F101 | Display List of All Videos                     | Completed | F003              |
| F102 | Input for Video Number (to check)              | Completed | F004              |
| F103 | Display Specific Video Details                 | Completed | F003, F102        |
| F104 | UI for Check Videos Module                     | Completed | F001              |
|      | **Create Video List Module** |           |                   |
| F201 | UI for Create Video List Module                | Pending   | F001              |
| F202 | Input for Video Number (to add to playlist)    | Pending   | F201              |
| F203 | Add Video to Playlist Logic                    | Pending   | F202, F003        |
| F204 | Display Current Playlist in Text Area          | Pending   | F201, F203        |
| F205 | "Play Playlist" Button & Logic (Increment Play Counts) | Pending   | F201, F203, F003  |
| F206 | "Reset Playlist" Button & Logic (Clear Playlist) | Pending   | F201, F204        |
|      | **Update Videos Module** |           |                   |
| F301 | UI for Update Videos Module                    | Completed | F001              |
| F302 | Input for Video Number (to update rating)      | Pending   | F301              |
| F303 | Input for New Rating                           | Pending   | F301              |
| F304 | "Update Rating" Button & Logic                 | Pending   | F302, F303, F003  |
| F305 | Display Update Confirmation Message            | Pending   | F304              |