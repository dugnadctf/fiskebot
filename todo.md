# TODO List

* [ ] Implement private channels for each CTF and problem
  * [ ] Archive channels after end of CTF
* [x] Set challenge length up to 20 characters
* [ ] Better state information per challenge in the mongodb
  * [ ] Implement solves from multiple people
  * [ ] Do not allow tampering with solves after it is solved. (maybe allow unsolve
    [ ] by admins, or by people who had access to channel before solve)
  * [ ] Save player statistics after CTF ends (do NOT delete all data on it)
* [ ] Sanitize challenge names
* [ ] Reply if a command is incomplete/command is invalid
* [ ] Should we only allow ctfbot be used in a bot-spam channel
* [ ] Syscall command, assembler handler
* [ ] setcreds command 
* [ ] mannage_channel permissions for ctf channels
  - @commands.has_permissions(manage_channels=True)
* env variables
   -     env_file:
      - bot-variables.env
* !sudo and !exit merge
* better permission system act on behalf of the user or lax mode where it just let's the user do pretty much anything
* only use !create outside of ctf channels