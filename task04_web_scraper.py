import tkinter as tk
from tkinter import ttk, filedialog
import threading, csv, os, json
import urllib.request, urllib.parse

BG      = "#070e1a"
CARD    = "#0c1729"
SURFACE = "#111f35"
ACCENT  = "#00d4e8"
DIM     = "#1a2d4a"
TEXT    = "#e8f4f8"
TEXT2   = "#5a8a9f"
TEXT3   = "#1e3a52"
GREEN   = "#00e5a0"
RED     = "#ff4d6d"
ORANGE  = "#ff8c42"

URL = "https://openlibrary.org/search.json?q={q}&limit={n}&fields=title,author_name,first_publish_year,ratings_average,subject"

class WebScraper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Web Data Scraper")
        self.geometry("820x620")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.results = []
        self._ui()

    def _ui(self):
        # header
        h = tk.Frame(self, bg=BG)
        h.pack(fill="x", padx=28, pady=(22,0))
        tk.Label(h, text="Web Data", bg=BG, fg=TEXT2,
                 font=("SF Pro Display","13")).pack(side="left")
        tk.Label(h, text=" Scraper", bg=BG, fg=TEXT,
                 font=("SF Pro Display","13","bold")).pack(side="left")
        tk.Label(h, text="Powered by Open Library API", bg=BG, fg=TEXT3,
                 font=("SF Pro Display","9")).pack(side="right")

        # search bar
        sb = tk.Frame(self, bg=CARD, padx=18, pady=14)
        sb.pack(fill="x", padx=28, pady=(16,0))
        tk.Label(sb, text="SEARCH QUERY", bg=CARD, fg=TEXT3,
                 font=("SF Pro Display","8")).pack(anchor="w")
        row = tk.Frame(sb, bg=CARD)
        row.pack(fill="x", pady=(6,0))
        self.query = tk.StringVar(value="machine learning")
        e = tk.Entry(row, textvariable=self.query, bg=SURFACE, fg=TEXT,
                     insertbackground=ACCENT, font=("SF Pro Display","13"),
                     bd=0, highlightthickness=0)
        e.pack(side="left", fill="x", expand=True, ipady=8, padx=(0,12))
        e.bind("<Return>", lambda _: self._scrape())

        tk.Label(row, text="Limit:", bg=CARD, fg=TEXT2,
                 font=("SF Pro Display","9")).pack(side="left", padx=(0,5))
        self.limit = tk.StringVar(value="20")
        tk.Spinbox(row, from_=5, to=50, increment=5, textvariable=self.limit,
                   width=4, bg=SURFACE, fg=TEXT, font=("SF Pro Display","11"),
                   bd=0, highlightthickness=0, buttonbackground=SURFACE,
                   insertbackground=ACCENT).pack(side="left", ipady=5, padx=(0,12))

        self.scrape_btn = tk.Button(row, text="Search & Scrape →", bg=ACCENT, fg=BG,
                                    font=("SF Pro Display","10","bold"), bd=0,
                                    padx=14, pady=6, cursor="hand2", relief="flat",
                                    command=self._scrape)
        self.scrape_btn.pack(side="left", padx=(0,8))

        self.export_btn = tk.Button(row, text="Export CSV", bg=DIM, fg=TEXT2,
                                    font=("SF Pro Display","10"), bd=0,
                                    padx=12, pady=6, cursor="hand2", relief="flat",
                                    command=self._export, state="disabled")
        self.export_btn.pack(side="left")

        # progress bar
        self.prog_c = tk.Canvas(self, height=3, bg=BG, highlightthickness=0)
        self.prog_c.pack(fill="x", padx=28, pady=(8,0))

        # table
        style = ttk.Style()
        style.theme_use("default")
        style.configure("S.Treeview", background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=28,
                        font=("SF Pro Display",10))
        style.configure("S.Treeview.Heading", background=SURFACE, foreground=ACCENT,
                        font=("SF Pro Display",9,"bold"), relief="flat")
        style.map("S.Treeview", background=[("selected", DIM)])

        cols = ("Title","Author","Year","Rating","Genre")
        tf = tk.Frame(self, bg=BG)
        tf.pack(fill="both", expand=True, padx=28, pady=(10,0))
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="S.Treeview")
        for col,w in zip(cols,[300,160,55,65,180]):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, minwidth=40)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # status
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=28, pady=(8,0))
        self.status = tk.Label(sf, text="Enter a query and hit Search & Scrape",
                               bg=BG, fg=TEXT2, font=("SF Pro Display","10"), anchor="w")
        self.status.pack(side="left")
        self.count = tk.Label(sf, text="", bg=BG, fg=TEXT3,
                              font=("SF Pro Display","9"))
        self.count.pack(side="right")

        tk.Label(self, text="Task 04  ·  Software Engineering Intern",
                 bg=BG, fg=TEXT3, font=("SF Pro Display","8")).pack(side="bottom", pady=8)

    def _scrape(self):
        q = self.query.get().strip()
        if not q:
            self.status.config(text="Please enter a search query", fg=ORANGE); return
        self.scrape_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.results.clear()
        for i in self.tree.get_children(): self.tree.delete(i)
        self.status.config(text=f"Fetching '{q}'…", fg=TEXT2)
        self._anim(0)
        threading.Thread(target=self._fetch, args=(q,), daemon=True).start()

    def _anim(self, pos):
        if not hasattr(self,'_animating') or not self._animating: return
        self.prog_c.update_idletasks()
        w = self.prog_c.winfo_width() or 760
        self.prog_c.delete("all")
        self.prog_c.create_rectangle(0,0,w,3,fill=DIM,outline="")
        bw = 120
        x = (pos % (w+bw)) - bw
        self.prog_c.create_rectangle(x,0,x+bw,3,fill=ACCENT,outline="")
        self.after(30, lambda: self._anim(pos+12))

    def _fetch(self, q):
        self._animating = True
        try:
            n = max(5,min(50,int(self.limit.get())))
        except: n=20
        url = URL.format(q=urllib.parse.quote(q), n=n)
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            rows = []
            for d in data.get("docs",[]):
                title  = d.get("title","—")[:70]
                author = ", ".join(d.get("author_name",["Unknown"]))[:50]
                year   = str(d.get("first_publish_year","—"))
                rat    = f"{d.get('ratings_average',0):.1f}★" if d.get("ratings_average") else "—"
                genre  = (d.get("subject") or ["—"])[0][:40]
                rows.append((title,author,year,rat,genre))
            self.after(0, lambda: self._populate(rows, q))
        except Exception as ex:
            self.after(0, lambda: self._err(str(ex)))

    def _populate(self, rows, q):
        self._animating = False
        self.prog_c.delete("all")
        self.results = rows
        for r in rows: self.tree.insert("","end",values=r)
        self.count.config(text=f"{len(rows)} records")
        self.status.config(text=f"✓  {len(rows)} results for '{q}'  —  ready to export", fg=GREEN)
        self.scrape_btn.config(state="normal")
        if rows: self.export_btn.config(state="normal")

    def _err(self, msg):
        self._animating = False
        self.prog_c.delete("all")
        self.status.config(text=f"Error: {msg}", fg=RED)
        self.scrape_btn.config(state="normal")

    def _export(self):
        if not self.results: return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv"),("All","*.*")],
            initialfile=f"scraped_{self.query.get().replace(' ','_')}.csv")
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Title","Author","Year","Rating","Genre"])
            w.writerows(self.results)
        self.status.config(text=f"Saved {len(self.results)} records → {os.path.basename(path)}", fg=ACCENT)

    def _sort(self, col):
        items = [(self.tree.set(k,col),k) for k in self.tree.get_children()]
        for i,(_,k) in enumerate(sorted(items)): self.tree.move(k,"",i)

if __name__=="__main__":
    WebScraper().mainloop()
