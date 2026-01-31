import dukpyra
app = dukpyra.app()

@app.get("/")
def home():
    return {"message": "Welcome to Dukpyra Test API", "version": "1.0", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": 1735891200, "uptime": 100}

@app.get("/api/info")
def api_info():
    return {"name": "Dukpyra Test API", "features": ["CRUD", "TypeSystem", "LINQ"], "author": "Test Suite"}

@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": "John Doe", "email": "john@example.com", "active": True}

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"post_id": post_id, "title": "Sample Post", "content": "This is a test post", "views": 42}

@app.get("/categories/{category_name}")
def get_category(category_name: str):
    return {"name": category_name, "description": "Category description", "item_count": 10}

@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id, "title": "User's Post", "author": "John Doe"}

@app.get("/organizations/{org_id}/teams/{team_id}")
def get_team(org_id: int, team_id: int):
    return {"org_id": org_id, "team_id": team_id, "team_name": "Development Team", "members": 5}

@app.post("/api/users")
def create_user():
    return {"id": 1, "name": "New User", "email": "newuser@example.com", "created": True, "timestamp": 1735891200}

@app.post("/api/posts")
def create_post():
    return {"id": 100, "title": "New Post", "content": "Post content here", "created": True}

@app.put("/api/users/{id}")
def update_user(id: int):
    return {"id": id, "name": "Updated User", "email": "updated@example.com", "updated": True}

@app.put("/api/posts/{id}")
def update_post(id: int):
    return {"id": id, "title": "Updated Post", "updated": True}

@app.delete("/api/users/{id}")
def delete_user(id: int):
    return {"id": id, "deleted": True, "message": "User deleted successfully"}

@app.delete("/api/posts/{id}")
def delete_post(id: int):
    return {"id": id, "deleted": True}

@app.patch("/api/users/{id}")
def patch_user(id: int):
    return {"id": id, "patched": True, "message": "User partially updated"}

@app.get("/api/stats")
def get_stats():
    return {"users": 1000, "posts": 5000, "comments": 25000, "average_posts_per_user": 5, "active_today": 150}

@app.get("/api/config")
def get_config():
    return {"app_name": "Dukpyra Test", "version": "1.0.0", "debug": False, "max_upload_size": 10485760}
