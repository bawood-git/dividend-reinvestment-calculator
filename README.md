Still in design phase. I'll publish documentation soon and a stable release after filling in some big blanks. 

This project is built on https://github.com/awesome-release/nginx-flask-mongo

This project is my introduction to Flask and Jinja. Wish me luck!

UPDATE! 20250303

I've got most of the UI wrinkles worked out and some objectives in mind for the simulation and data exports.

*  Add a manual configuration option for linear simulations
*  Configure a few more API sources with at least one free option
*  Include more data calculations, specifically EPS and price history to get a historical tend and create what if? scenarios
*  Add BookStack for documentation and per-user notes as well as Hashgicorp Vault for storing secrets.
*  Theme supporrt. At least a light/dark mode
*  Accessibility features are missing. I'd love to recruit someone to help guide me in a way that makes sense. Short of that, I will make an attempt.
*  Admin init on new deploy to set up secrets once a vault is added to the project

Known issues (not in order of importance) 
*  Forms: CSRF refresh timing
*  Pages: Help section is missing. I will add BookStack for deep dives into documentation and logic explanation
*  Options:
  *  Data exports are incomplete
  *  PDF export is functional, though I'd like to change the layout before calling it complete
  *  CSV export is not functional. I need to develop a temp file solution, so storage will be limited to something like last 10 exports
  *  JSON export is not funcional. I experimented with a few options and I think I want this to be two things:
     # UI Report -> target="_blank" for a text copy/paste page load
     # Console /endpoint for middleware scripting (med-long project later this year) 
*  Settings: Preferences are meh. 
*  System Components:
   *  SSL not included until I build a default end-to-end self signed certificae script in Docker
   *  Authentication is just a local file session store until SSL implemented

 
Screenshots:

![image](https://github.com/user-attachments/assets/b2a98487-ec42-4991-a6e1-bfaf52d8b39f)

![image](https://github.com/user-attachments/assets/639d574d-363f-4151-8462-5ba3be609302)
