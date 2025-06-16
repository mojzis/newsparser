---
author: André Carlos Jr.
domain: dotproj.ac-jr.com
evaluation:
  evaluated_at: '2025-06-13T23:09:59.298170Z'
  evaluator: claude-3-haiku-20240307
  is_mcp_related: false
  key_topics:
  - dotfiles
  - project configuration management
  - git
  perex: Dotfiles, dotfiles everywhere! DotProj is here to tame the chaos of your
    project configs.
  relevance_score: 0.1
  summary: The article describes a tool called DotProj that helps manage project-specific
    configuration files across multiple projects.
extraction_timestamp: '2025-06-13T23:07:07.653275Z'
fetch_status: success
fetched_at: '2025-06-13T23:07:07.653309Z'
found_in_posts:
- at://did:plc:n2rywfeyu4zry542k24b5fbx/app.bsky.feed.post/3lrceqmnejk2d
language: null
medium: null
stage: evaluated
title: DotProj - Manage Your Dotfiles and Configurations Across Projects
url: https://dotproj.ac-jr.com/
word_count: 272
---

# DotProj - Manage Your Dotfiles and Configurations Across Projects

curl -fsSL https://raw.githubusercontent.com/andrecrjr/dotproj/master/install.sh | bash ✅ Binary installed to ~/.dotproj/dotproj ✅ Added to PATH: export PATH="$HOME/.dotproj:$PATH" source ~/.bashrc dotproj version 🎯 DotProj - Project-Specific Configuration Manager Version: 1.0.0 ✅ Setup complete\! You're ready to start using DotProj.

dotproj init my-config https://github.com/user/my-config.git Creating project structure... Initializing Git repo... ✅ Initialized project 'my-config' .env.local, .vscode/, .cursorrules, .prettierrc ✅ Added: .env.local ✅ Added: .vscode/ ✅ Added: .cursorrules ✅ Added: .prettierrc dotproj commit my-config 🔗 Committed: .env.local 🔗 Committed: .vscode/settings.json 🔗 Committed: .cursorrules 🔗 Committed: .prettierrc ✅ Committed files/dotfiles for 'my-config' dotproj push my-config 🚀 Pushing files/dotfiles for 'my-config'... ✅ Successfully pushed to remote

dotproj clone team-project https://github.com/team/project-configs.git 📥 Cloning repository to dotproj storage... ✅ Repository cloned successfully\! 1\) dotproj-frontend ⭐ \(DotProj branch\) 2\) dotproj-backend ⭐ \(DotProj branch\) 3\) dotproj-fullstack ⭐ \(DotProj branch\) 4\) main 1 ✅ Selected branch: dotproj-frontend y 🔗 Committed: .vscode/settings.json 🔗 Committed: .env.local 🔗 Committed: .cursor 🎉 Clone and commit complete\!

dotproj add my-config ✅ .env.local ✅ .vscode/settings.json .eslintrc.js, .gitignore, docker-compose.override.yml ✅ Added: .eslintrc.js ✅ Added: .gitignore ✅ Added: docker-compose.override.yml dotproj status my-config ✅ .env.local ✅ .vscode/settings.json ✅ .eslintrc.js ✅ .gitignore dotproj list \- my-config \- team-project

dotproj pull my-config 1\) dotproj-frontend ⭐ \(DotProj branch\) 2\) dotproj-backend ⭐ \(DotProj branch\) 3\) main 2 ✅ Selected branch: dotproj-backend ✅ Successfully pulled from remote y 🔗 Committed: .env 🔗 Committed: package.json ✅ Committed files/dotfiles for 'my-config' dotproj push my-config 🚀 Pushing files/dotfiles for 'my-config'... ✅ Successfully pushed to remote ✅ Push completed for 'my-config'