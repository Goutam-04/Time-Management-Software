// scripts/data_generator.js
// Merges raw data files into the main 'data.json' for the solver.

const fs = require('fs');

const thirdBtechTT = {
  "CSE A": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "To Be Assigned", "room": "B-209" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "12:00 PM - 1:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "12:00 PM - 1:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "To Be Assigned", "room": "B-209" }
    ]
  },
  "CSE B": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "To Be Assigned", "room": "B-209" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "B-209" },
      { "time": "3:00 PM - 4:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "4:00 PM - 5:00 PM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "GF5", "room": "B-209" },
      { "time": "12:00 PM - 1:00 PM", "status": "Assigned", "subject": "EE", "teacher": "RS2", "room": "B-209" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ]
  },
  "CSE (AIML)": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "SKPn", "room": "A-32" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Assigned", "subject": "EE", "teacher": null, "room": "A-32" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Assigned", "subject": "MATH", "teacher": "SKPn", "room": "A-32" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "10:00 AM - 11:00 AM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "4:00 PM - 5:00 PM", "status": "Assigned", "subject": "EE", "teacher": null, "room": "A-32" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "10:00 AM - 11:00 AM", "status": "Assigned", "subject": "MATH", "teacher": "SKPn", "room": "A-32" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Assigned", "subject": "EE", "teacher": null, "room": "A-32" },
      { "time": "3:00 PM - 4:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "12:00 PM - 1:00 PM", "status": "To Be Assigned", "room": "A-32" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ]
  }
};

const fifthBtechTT = {
  "CSE": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Assigned", "subject": "ISE", "teacher": null, "room": "B205" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Assigned", "subject": "ED", "teacher": null, "room": "B205" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Assigned", "subject": "ISE", "teacher": null, "room": "B205" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Assigned", "subject": "ED", "teacher": null, "room": "B205" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ]
  },
  "CSE (AI/ML)": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Assigned", "subject": "ISE", "teacher": null, "room": "B205" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Assigned", "subject": "ISE", "teacher": null, "room": "B 205" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Assigned", "subject": "ED", "teacher": null, "room": "B205" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:0D:00 PM - 5:00 PM", "status": "Free" }
    ]
  }
};

const seventhBtechTT = {
  "CSE": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ]
  },
  "IT": {
    "Monday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Tuesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Wednesday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Thursday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ],
    "Friday": [
      { "time": "9:00 AM - 10:00 AM", "status": "Free" },
      { "time": "10:00 AM - 11:00 AM", "status": "Free" },
      { "time": "11:00 AM - 12:00 PM", "status": "Free" },
      { "time": "12:00 PM - 1:00 PM", "status": "Free" },
      { "time": "2:00 PM - 3:00 PM", "status": "Free" },
      { "time": "3:00 PM - 4:00 PM", "status": "Free" },
      { "time": "4:00 PM - 5:00 PM", "status": "Free" }
    ]
  }
};

// ----------------- START OF MERGE AND RESTRUCTURE CODE (FIXED) -----------------

const allTimeTables = {
    // We map the object names directly to the correct semester number
    "thirdBtechTT": { data: thirdBtechTT, year: 3 },
    "fifthBtechTT": { data: fifthBtechTT, year: 5 },
    "seventhBtechTT": { data: seventhBtechTT, year: 7 }
};

const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

// Helper function to convert "9:00 AM - 10:00 AM" to "9-10"
function formatTimeKey(time) {
    const match = time.match(/(\d+):\d+\s+(?:AM|PM)\s+-\s+(\d+)/);
    if (match) {
        return `${match[1]}-${match[2]}`;
    }
    return time;
}

// Function to extract the semester number (last part of the section string)
function getSemester(section) {
    const parts = section.split('-');
    // The semester number is the last element
    return parseInt(parts[parts.length - 1]);
}

/**
 * Reshapes all timetable data into the new structure:
 * { "Monday": [ { "section": "...", "9-10": [...], "10-11": [...] }, ... ] }
 * while handling sorting (3rd -> 5th -> 7th).
 * @param {object} allTTs - The map of all time table objects with their years.
 * @returns {object} The restructured data.
 */
function restructureTimeTable(allTTs) {
    const restructuredData = {};
    const sectionOrder = [];

    // Step 1: Process and group the data by Day, then by Section
    for (const { data: ttData, year } of Object.values(allTTs)) {
        
        for (const sectionName in ttData) {
            if (ttData.hasOwnProperty(sectionName)) {
                const sectionData = ttData[sectionName];
                
                // FIXED: Now uses the correct 'year' variable for the section code
                const sectionCode = `${sectionName.replace(/[()\s/]/g, '-')}-${year}`.replace(/--/g, '-').replace(/-$/, '');

                // Add to section order list for later sorting
                sectionOrder.push({ section: sectionCode, year: year });

                for (const day of daysOfWeek) {
                    if (sectionData[day]) {
                        if (!restructuredData[day]) {
                            restructuredData[day] = {};
                        }

                        // Initialize the section entry for the day if it doesn't exist
                        if (!restructuredData[day][sectionCode]) {
                            restructuredData[day][sectionCode] = { section: sectionCode };
                        }

                        sectionData[day].forEach(period => {
                            const timeKey = formatTimeKey(period.time);
                            const periodDetails = { status: period.status };

                            // Include room if available and not explicitly empty for Free slots
                            if (period.room && period.status !== "Free") {
                                periodDetails.room = period.room;
                            } else if (period.status === "To Be Assigned" && period.room) {
                                periodDetails.room = period.room; // Keep room for planning slots
                            }
                            
                            // Add subject/teacher if assigned
                            if (period.status === "Assigned") {
                                periodDetails.subject = period.subject;
                                periodDetails.teacher = period.teacher !== undefined ? period.teacher : null;
                            }

                            // Add the period details to the time slot array
                            if (!restructuredData[day][sectionCode][timeKey]) {
                                restructuredData[day][sectionCode][timeKey] = [];
                            }
                            restructuredData[day][sectionCode][timeKey].push(periodDetails);
                        });
                    }
                }
            }
        }
    }

    // Step 2: Flatten and Sort the Data
    const finalData = {};
    
    // Sort sections: 3rd year first, then 5th, then 7th, then alphabetically within the same year.
    const uniqueSortedSections = Array.from(new Set(sectionOrder.map(s => s.section)))
        .map(section => ({ section, year: getSemester(section) }))
        .sort((a, b) => {
            if (a.year !== b.year) {
                return a.year - b.year; // Sort by year (3, 5, 7)
            }
            return a.section.localeCompare(b.section); // Sort alphabetically by section name
        })
        .map(s => s.section);

    for (const day of daysOfWeek) {
        if (restructuredData[day]) {
            finalData[day] = [];
            
            // Reorder sections based on the pre-sorted list (3, 5, 7)
            for (const sectionCode of uniqueSortedSections) {
                if (restructuredData[day][sectionCode]) {
                    finalData[day].push(restructuredData[day][sectionCode]);
                }
            }
        }
    }

    return finalData;
}

const finalTimeTableData = restructureTimeTable(allTimeTables);

// Convert the merged data to a JSON string with indentation for readability
const jsonContent = JSON.stringify(finalTimeTableData, null, 2);

// UPDATED PATH: Write the JSON string to data/data.json
const fileName = 'data/data.json';
try {
    fs.writeFileSync(fileName, jsonContent);
    console.log(`✅ Successfully fixed and restructured time tables (3rd, 5th, 7th year order) and saved to ${fileName}`);
} catch (error) {
    console.error(`❌ Error writing file ${fileName}:`, error);
}

// ----------------- END OF MERGE AND RESTRUCTURE CODE (FIXED) -----------------