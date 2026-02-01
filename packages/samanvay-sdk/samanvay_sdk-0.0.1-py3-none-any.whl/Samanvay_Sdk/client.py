class Client:
    def __init__(self):
        pass  # no args needed, data is pre-filled

    def _hyperlink(self, url: str, text: str = None) -> str:
        """Create clickable link with fallback for terminals."""
        if text is None:
            text = url
        # ANSI OSC 8 hyperlink - works in iTerm2, VSCode, Windows Terminal, WezTerm
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

    # ---- Socials ----
    def get_linkedin(self):
        url = "https://www.linkedin.com/in/samanvay-kumar-tadakamalla/"
        return f"LinkedIn : {self._hyperlink(url, url)}"

    def get_github(self):
        url = "https://github.com/samanvay-kumar"
        return f"GitHub   : {self._hyperlink(url, url)}"

    def get_twitter(self):
        url = "https://x.com/samanvay__06"
        return f"Twitter  : {self._hyperlink(url, url)}"

    def get_leetcode(self):
        url = "https://leetcode.com/u/samanvay__06/"
        return f"LeetCode : {self._hyperlink(url, url)}"

    def get_medium(self):
        url = "https://medium.com/@t.samanvaykumar"
        return f"Medium   : {self._hyperlink(url, url)}"
    
    def get_reddit(self):
        url = "https://www.reddit.com/user/samanvay_06/"
        return f"Reddit   : {self._hyperlink(url, url)}"

    # ---- Identity ----
    def get_full_name(self):
        return "Tadakamalla Samanvay Kumar"

    def get_name(self):
        return "Samanvay Kumar"
    
    # ---- Author Info ----
    def get_author_info(self):
        return (
            "Hello! I am Samanvay Kumar Tadakamalla.\n"
            "I’m working toward becoming an AI/ML engineer, and I learn best by actually building things. "
            "I stay motivated by curiosity and by seeing how ideas work in practice. "
            "I am actively exploring the field of Artificial Intelligence, focusing on building a strong foundation "
            "and growing steadily at my own pace.\n\n"
            "Instead of only reading about new advancements, I like to dive in—whether it's coding in Python and C++, "
            "working with MySQL, or understanding how Generative AI models operate.\n\n"
            "I’m a student at NIAT, and I currently work as the Operations Manager of the Gen AI Club. "
            "I spend part of my time helping with organizing activities, coordinating sessions, and contributing "
            "wherever I can to keep the club running smoothly.\n\n"
            "I'm driven by the satisfaction that comes from solving tough technical problems, and I'm always "
            "looking for the next opportunity to learn, build, and improve."
        )
    
    def about_sdk(self):
        return (
            "Samanvay-Sdk is a Python package that provides easy access to "
            "Samanvay Kumar Tadakamalla's professional and social information "
            "through simple function calls. It includes methods to retrieve "
            "clickable links to his social media profiles, along with his full "
            "name, education, and author bio. This SDK is designed for people "
            "who want to access this information programmatically."
        )
    
    def get_education(self):
        return (
            "NIAT student (2nd year) pursuing a B.Sc degree in "
            "Computer Science and Engineering through BITS Pilani."
        )
