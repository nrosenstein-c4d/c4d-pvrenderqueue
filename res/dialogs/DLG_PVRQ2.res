// C4D-DialogResource
DIALOG DLG_PVRQ2
{
  NAME IDS_DIALOG; SCALE_V; SCALE_H; 
  
  GROUP 
  {
    SCALE_V; SCALE_H; 
    BORDERSIZE 4, 4, 4, 4; 
    COLUMNS 1;
    SPACE 4, 4;
    
    GROUP 
    {
      NAME IDS_STATIC1; ALIGN_TOP; SCALE_H; 
      BORDERSIZE 0, 0, 0, 0; 
      ROWS 1;
      SPACE 4, 4;
      
      BITMAPBUTTON BTN_START
      {
        CENTER_V; ALIGN_LEFT; 
        BUTTON; 
        ICONID1 5140; 
        ICONID2 0; 
        SIZE 0, 0; 
        SPECIAL 0; 
      }
      STATICTEXT  { NAME IDS_STATIC3; CENTER_V; SCALE_H; }
      BITMAPBUTTON BTN_ADD_FILE
      {
        CENTER_V; ALIGN_LEFT; 
        BUTTON; 
        ICONID1 5140; 
        ICONID2 0; 
        SIZE 0, 0; 
        SPECIAL 0; 
      }
      BITMAPBUTTON BTN_ADD_FOLDER
      {
        CENTER_V; ALIGN_LEFT; 
        BUTTON; 
        ICONID1 5140; 
        ICONID2 0; 
        SIZE 0, 0; 
        SPECIAL 0; 
      }
    }
    TREEVIEW GUI_TREEVIEW
    {
      SCALE_V; SCALE_H; 
      BORDER; 
      HAS_HEADER; 
      NOENTERRENAME; 
    }
  }
}