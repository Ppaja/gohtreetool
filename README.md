![Screenshot](screen.jpg)

### Visual GoH dc research tree editor
<details>
  <summary>Screenshots</summary>

  ![Screenshot 1](imgs/s1.jpg)  
  ![Screenshot 2](imgs/s2.jpg)  
  ![Screenshot 3](imgs/s3.jpg)  

</details>

Inside the mod folder is the current version of the mod, you can just modify it for a american, fin etc tree. If you have a question ask me ^^

## Usage

(0. [download](https://github.com/Ppaja/gohtreetool/archive/refs/heads/main.zip) this repo)
1. **Select the Correct Research File**: 
   Open the `sc.py` script and modify the line to select the correct research file for the nation you want to edit. For example:

   ```python
   editor = TreeEditor("unit_research_ger.set")  # <--------- modify line 268
   ```

   - German: `unit_research_ger.set`
   - Finland: `unit_research_fin.set`
   - Russia: `unit_research_rus.set`
   - USA: `unit_research_usa.set`

2. **Run the Script**:
   Execute the script to open the visual editor:

   ```bash
   python sc.py
   ```

   Or run one of the .bat files.

3. **Edit the Research Tree**:
   Use the graphical interface to modify the research tree:
   -drag and drop research items to new positions
   -double click on a research item to edit the cost and the requires field
     --cost: simply change the number and save
     --requires: type in the unit name from the gamefile and save or click the + button and klick on the unit you want to add as a requirement
   -hold "v" to display the current connections 

4. **Save Your Changes**:
   Click the "Save Changes" button to update the research file with your new layout.

5. **Export to Mod Folder**:
   Copy the modified research file to the mod's `\resource\set\dynamic_campaign` folder.
   The mod folder can now be uploaded to workshop with your design of the research tree 

