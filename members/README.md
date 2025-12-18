# 🤖 Robotics Team Sandbox

Welcome to the members' directory! This is where you can experiment, write your own sub-systems, and test logic without breaking the main robot code.

## 📂 How to use this folder
1. **Create your folder:** Create a folder here named after yourself (e.g., `/members/sarahs_folder`).
2. **Stay in your lane:** Try to keep your experimental scripts inside your own folder.
3. **Common Root:** If you have finalised some code and its ready for the real the robot, edit the files in the `/root` or `/src` folder, then open a **Pull Request** on the GitHub website.

## 🚀 The Workflow
To keep the robot's "brain" healthy, please follow these steps:

1. **Branch:** Never work directly on `main`. Switch to your branch: 
   `git checkout yourname-feature`
   If you want to check which brach you're on:
   `git branch`
2. **Commit & Push:** Save your work and send it to GitHub:
   `git add .`
   `git commit -m "Added lift sensor logic"`
   `git push origin yourname-feature`
3. **Pull Request:** Once your code is tested and ready for the real robot, open a **Pull Request** on GitHub to merge it into `main`.

---
*Questions? Ask @Adam*