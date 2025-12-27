# UniBots | 2025-2026 Season
Official repository for the KCL UniBots Team 6! This project contains the core robot controller logic and individual member sandboxes. If you are a member of the team 6 please follow the instructions below.

## Instructions

### 1. Join GitHub Repo (to add your code)
* Create a [GitHub account](https://github.com)
* Message me (**Adam**) the account username so I can add you format: `GitHub Username: <your username>`

### 2. Join ClickUp Team (to see what needs to be done)
* Create a [ClickUp acount](https://clickup.com)
* Message me (**Adam**) the account email so I can add you format: `ClickUp Email: <your email>`

### 3. Join Fusion Team (to access 3D models)
* Make sure you have a **Fusion360** account with the [Education License](https://www.autodesk.com/uk/education/edu-software/fusion)
* Message me (**Adam**) the account email so I can add you format: `Fusion Email: <your email>`

### 4. Create your own branch
* On this page click `main` (top left)
* Click view all branches
* Click `New Branch` (If this doesnt appear I haven't added you yet, in the meantime move on to the next step)
* yournames_branch

### 5. Clone Git Repository
1. Dowload [VS Code](https://code.visualstudio.com)
2. Dowload [Git](https://git-scm.com/install/mac)
3. On this page click the green button `<> Code`
4. Copy the **HTTPS URL**
5. Open **VS Code**
6. Click Clone Git Repository (if this doesn't appear it's beacuse you havent installed Git correctly, troubleshoot with a chatbot)
7. Paste the **HTTPS URL**
8. Chose where you want the folder to appear

### 6. Create your first file
1. In the members folder create a personal folder (e.g., adams_folder). This is where you will store your individual code.
2. Create a dummy file inside this folder (e.g., `test.py` or `hello.txt`).
3. Open **VS Code** and select **Open Folder**, then choose the UniBots directory.
4. Open the terminal by pressing `Ctrl + J` (Windows) or `Cmd + J` (Mac).
5. Type `git fetch origin` to make sure your computer sees the branch you created on the website.
6. Type `git branch`. An asterisx (*) should appear next to main
7. Type `git switch yournames_branch`. This moves you from the "official" code to your personal workspace.
8. Type `git add .` to prepare your new folder and file for saving.
9. Type `git commit -m "initial setup"` to save those changes locally (you can change "inital setup" to whaetver message you want, just make sure you use "").
10. Type `git push origin yournames_branch` to send your work to GitHub.
11. Have a look on the GitHub website on your branch to see if your folder appears!



## Contribution Rules
To prevent breaking the robot during testing, we follow these rules:
* **Work in your own branch:** When you are testing out your code, make sure you are in your own branch (`git switch your_branch`).
* **No Direct Pushes:** All changes to the `main` branch must come through a **Pull Request**.
* **Personal Work:** Keep your experimental code inside your folder in `/members`.
* **Code Review:** At least one other team member must review a PR before it is merged for a competition build.

*Questions? Ask @Adam-Axelrod*
