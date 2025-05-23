import tkinter as tk

import font_manager as fonts
import video_library as lib


class UpdateVideos():
    def __init__(self, window):
        window.geometry("400x250")
        window.title("Update Videos")

        # Header label
        header_lbl = tk.Label(window, text="Update Video Rating")
        header_lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Video number input
        enter_video_lbl = tk.Label(window, text="Enter Video Number")
        enter_video_lbl.grid(row=1, column=0, padx=10, pady=10)

        self.video_input_txt = tk.Entry(window, width=5)
        self.video_input_txt.grid(row=1, column=1, padx=10, pady=10)

        # Rating input
        enter_rating_lbl = tk.Label(window, text="Enter New Rating")
        enter_rating_lbl.grid(row=2, column=0, padx=10, pady=10)

        self.rating_input_txt = tk.Entry(window, width=5)
        self.rating_input_txt.grid(row=2, column=1, padx=10, pady=10)

        # Update button
        update_btn = tk.Button(window, text="Update Rating", command=self.update_rating_clicked)
        update_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Result display area
        self.result_txt = tk.Text(window, width=40, height=6, wrap="word")
        self.result_txt.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        # Status label
        self.status_lbl = tk.Label(window, text="", font=("Helvetica", 10))
        self.status_lbl.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

    def update_rating_clicked(self):
        video_key = self.video_input_txt.get().strip()
        rating_text = self.rating_input_txt.get().strip()

        # Clear previous result
        self.result_txt.delete("1.0", tk.END)

        # Validate inputs
        if not video_key:
            self.result_txt.insert("1.0", "Error: Please enter a video number.")
            self.status_lbl.configure(text="Update failed - missing video number")
            return

        if not rating_text:
            self.result_txt.insert("1.0", "Error: Please enter a rating.")
            self.status_lbl.configure(text="Update failed - missing rating")
            return

        # Validate rating is a number
        try:
            new_rating = int(rating_text)
        except ValueError:
            self.result_txt.insert("1.0", "Error: Rating must be a number.")
            self.status_lbl.configure(text="Update failed - invalid rating format")
            return

        # Check if video exists
        video_name = lib.get_name(video_key)
        if video_name is None:
            self.result_txt.insert("1.0", f"Error: Video {video_key} not found.")
            self.status_lbl.configure(text="Update failed - video not found")
            return

        # Update the rating
        lib.set_rating(video_key, new_rating)
        
        # Get updated information for confirmation
        play_count = lib.get_play_count(video_key)
        
        # Display confirmation message
        confirmation_message = f"Successfully updated!\n\n"
        confirmation_message += f"Video: {video_name}\n"
        confirmation_message += f"New Rating: {new_rating}\n"
        confirmation_message += f"Play Count: {play_count}"
        
        self.result_txt.insert("1.0", confirmation_message)
        self.status_lbl.configure(text="Rating updated successfully!")

        # Clear input fields
        self.video_input_txt.delete(0, tk.END)
        self.rating_input_txt.delete(0, tk.END)


if __name__ == "__main__":  # only runs when this file is run as a standalone
    window = tk.Tk()  # create a TK object
    fonts.configure()  # configure the fonts
    UpdateVideos(window)  # open the UpdateVideos GUI
    window.mainloop()  # run the window main loop, reacting to button presses, etc 