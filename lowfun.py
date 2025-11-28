from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import time
import hashlib
import secrets
import random
import string
import os

CONFIG = {
    "admin_password": "hvk2osjm",
    "host": "0.0.0.0",
    "port": int(os.environ.get("PORT", 8000))
}

data = {
    "users": {},
    "threads": [],
    "comments": {},
    "invites": ['welcome1'],
    "sessions": {}
}


class LowFunForum(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.serve_main_page()
        elif self.path == '/admin':
            self.serve_admin_page()
        elif self.path.startswith('/login'):
            self.serve_login_page()
        elif self.path.startswith('/register'):
            self.serve_register_page()
        elif self.path.startswith('/logout'):
            self.handle_logout()
        elif self.path.startswith('/thread/'):
            self.serve_thread_page()
        else:
            self.serve_main_page()

    def do_POST(self):
        if self.path == '/post':
            self.handle_post()
        elif self.path == '/comment':
            self.handle_comment()
        elif self.path == '/login':
            self.handle_login()
        elif self.path == '/register':
            self.handle_register()
        elif self.path == '/admin/generate_invite':
            self.generate_invite()
        elif self.path == '/admin/delete_thread':
            self.delete_thread()
        elif self.path == '/admin/delete_comment':
            self.delete_comment()
        else:
            self.send_error(404)

    def get_current_user(self):
        session_id = self.get_cookie('session_id')
        if session_id and session_id in data['sessions']:
            return data['sessions'][session_id]
        return None

    def get_cookie(self, name):
        cookie_header = self.headers.get('Cookie', '')
        cookies = cookie_header.split(';')
        for cookie in cookies:
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                if key == name:
                    return value
        return None

    def set_cookie(self, name, value):
        self.send_header('Set-Cookie', f'{name}={value}; Path=/')

    def get_error_message(self):
        query = urlparse.urlparse(self.path).query
        params = urlparse.parse_qs(query)
        error = params.get('error', [''])[0]

        error_messages = {
            'invalid_password': 'Invalid password',
            'user_not_found': 'User does not exist',
            'user_exists': 'Username already taken',
            'invalid_invite': 'Invalid invite code'
        }

        return error_messages.get(error, '')

    def serve_main_page(self):
        user = self.get_current_user()

        if not user:
            self.send_html('''
<!DOCTYPE html>
<html>
<head>
    <title>lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; line-height: 1.4; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; padding: 40px 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 40px; }
        .logo { font-size: 48px; font-weight: 900; margin-bottom: 20px; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        .nav { margin: 30px 0; }
        .nav a { color: #8b5cf6; text-decoration: none; margin: 0 15px; font-weight: 500; }
        .nav a:hover { color: #a78bfa; }
        .content { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 40px; text-align: center; }
        .message { font-size: 18px; color: #94a3b8; margin-bottom: 30px; }
        .back-link { color: #8b5cf6; text-decoration: none; font-weight: 500; }
        .back-link:hover { color: #a78bfa; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #2a2a2a; color: #64748b; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo" onclick="window.location.href='/'">
                <span class="white">low</span><span class="purple">fun</span>
            </div>
            <div class="nav">
                <a href="/register">Register</a>
                <a href="/login">Login</a>
            </div>
        </div>

        <div class="content">
            <div class="message">You are not logged in.</div>
            <div style="height: 2px; background: linear-gradient(90deg, transparent, #8b5cf6, transparent); margin: 30px 0;"></div>
            <h3 style="color: #8b5cf6; margin-bottom: 20px;">Info</h3>
            <p style="color: #94a3b8; margin-bottom: 30px;">You do not have permission to view these forums.</p>
            <a href="/" class="back-link">Go back</a>
        </div>

        <div class="footer">
            lowfun • 2025
        </div>
    </div>
</body>
</html>''')
        else:
            # Build HTML for logged in users
            html_parts = []
            html_parts.append('''
<!DOCTYPE html>
<html>
<head>
    <title>lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; line-height: 1.4; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 30px; }
        .logo { font-size: 28px; font-weight: 900; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        .nav a { color: #8b5cf6; text-decoration: none; margin-left: 20px; font-weight: 500; }
        .nav a:hover { color: #a78bfa; }
        .thread { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; margin-bottom: 15px; cursor: pointer; transition: all 0.2s; }
        .thread:hover { border-color: #8b5cf6; transform: translateY(-2px); }
        .thread-title { font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #f1f5f9; }
        .thread-meta { color: #8b5cf6; font-size: 13px; margin-bottom: 12px; }
        .thread-preview { color: #94a3b8; line-height: 1.5; font-size: 14px; }
        .thread-stats { color: #64748b; font-size: 12px; margin-top: 10px; }
        .create-thread { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .create-thread input, .create-thread textarea { width: 100%; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; padding: 12px; color: #fff; margin-bottom: 12px; font-family: inherit; }
        .create-thread input:focus, .create-thread textarea:focus { outline: none; border-color: #8b5cf6; }
        .create-thread button { background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-family: inherit; font-weight: 500; }
        .create-thread button:hover { background: #7c3aed; }
        .admin-panel { background: #1e1b4b; border: 1px solid #3730a3; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .invite-code { background: #0a0a0a; padding: 8px 12px; border-radius: 4px; font-family: monospace; margin: 5px 0; color: #8b5cf6; }
        .delete-btn { background: #dc2626; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-left: 10px; }
        .delete-btn:hover { background: #b91c1c; }
        .user-badge { background: #8b5cf6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
        .welcome-text { color: #8b5cf6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo" onclick="window.location.href='/'">
                <span class="white">low</span><span class="purple">fun</span>
            </div>
            <div class="nav">
                <span class="welcome-text">welcome, ''' + user + '''</span>
                <a href="/logout">logout</a>''')

            if user == 'riversize':
                html_parts.append('<a href="/admin">admin</a>')

            html_parts.append('''
            </div>
        </div>''')

            if user:
                html_parts.append('''
        <div class="create-thread">
            <form method="post" action="/post">
                <input type="text" name="title" placeholder="thread title" required>
                <textarea name="content" rows="3" placeholder="your message" required></textarea>
                <button type="submit">create thread</button>
            </form>
        </div>''')

                if user == 'riversize':
                    invites_html = "".join('<div class="invite-code">' +
                                           invite + '</div>'
                                           for invite in data["invites"])
                    html_parts.append('''
        <div class="admin-panel">
            <h3 style="margin-bottom: 10px; color: #8b5cf6;">admin panel</h3>
            <form method="post" action="/admin/generate_invite" style="display: inline;">
                <button type="submit">generate invite</button>
            </form>
            <div style="margin-top: 10px;">
                <strong style="color: #c4b5fd;">active invites:</strong>
                ''' + invites_html + '''
            </div>
        </div>''')

            if data['threads']:
                for thread in reversed(data['threads']):
                    delete_button = ''
                    if user == 'riversize':
                        delete_button = '<form method="post" action="/admin/delete_thread" style="display: inline;"><input type="hidden" name="thread_id" value="' + str(
                            thread["id"]
                        ) + '"><button type="submit" class="delete-btn">delete</button></form>'

                    admin_badge = ' <span class="user-badge">admin</span>' if thread[
                        'author'] == 'riversize' else ''
                    comment_count = len(data['comments'].get(thread['id'], []))
                    preview = thread['content'][:100] + ('...' if len(
                        thread['content']) > 100 else '')

                    html_parts.append(
                        '''
        <div class="thread" onclick="window.location.href='/thread/''' +
                        str(thread['id']) + '''">
            <div class="thread-title">''' + self.escape_html(thread['title']) +
                        '''</div>
            <div class="thread-meta">
                by ''' + thread['author'] + admin_badge + ''' • ''' +
                        time.strftime('%Y-%m-%d %H:%M',
                                      time.localtime(thread['timestamp'])) +
                        '''
                ''' + delete_button + '''
            </div>
            <div class="thread-preview">''' + self.escape_html(preview) +
                        '''</div>
            <div class="thread-stats">
                ''' + str(comment_count) + ''' comment''' +
                        ('s' if comment_count != 1 else '') + '''
            </div>
        </div>''')
            else:
                html_parts.append('''
        <div class="thread">
            <div class="thread-preview" style="text-align: center; color: #64748b; padding: 40px;">
                no threads yet. be the first to post something.
            </div>
        </div>''')

            html_parts.append('''
    </div>
</body>
</html>''')

            self.send_html(''.join(html_parts))

    def serve_thread_page(self):
        user = self.get_current_user()
        if not user:
            self.redirect('/login')
            return

        thread_id = int(self.path.split('/')[-1])
        thread = next((t for t in data['threads'] if t['id'] == thread_id),
                      None)

        if not thread:
            self.redirect('/')
            return

        comments = data['comments'].get(thread_id, [])

        html_parts = []
        html_parts.append('''
<!DOCTYPE html>
<html>
<head>
    <title>''' + self.escape_html(thread['title']) + ''' - lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; line-height: 1.4; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 30px; }
        .logo { font-size: 28px; font-weight: 900; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        .nav a { color: #8b5cf6; text-decoration: none; margin-left: 20px; font-weight: 500; }
        .nav a:hover { color: #a78bfa; }
        .thread-detail { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 25px; margin-bottom: 20px; }
        .thread-title { font-size: 22px; font-weight: 600; margin-bottom: 15px; color: #f1f5f9; }
        .thread-meta { color: #8b5cf6; font-size: 14px; margin-bottom: 15px; }
        .thread-content { color: #94a3b8; line-height: 1.6; margin-bottom: 20px; }
        .comments-section { margin-top: 30px; }
        .comment { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .comment-meta { color: #8b5cf6; font-size: 13px; margin-bottom: 10px; }
        .comment-content { color: #94a3b8; line-height: 1.5; }
        .add-comment { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .add-comment textarea { width: 100%; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; padding: 12px; color: #fff; margin-bottom: 12px; font-family: inherit; min-height: 80px; }
        .add-comment textarea:focus { outline: none; border-color: #8b5cf6; }
        .add-comment button { background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-family: inherit; font-weight: 500; }
        .add-comment button:hover { background: #7c3aed; }
        .delete-btn { background: #dc2626; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-left: 10px; }
        .delete-btn:hover { background: #b91c1c; }
        .user-badge { background: #8b5cf6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px; }
        .back-link { color: #8b5cf6; text-decoration: none; font-weight: 500; margin-bottom: 20px; display: inline-block; }
        .back-link:hover { color: #a78bfa; }
        .welcome-text { color: #8b5cf6; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← back to all threads</a>
        <div class="header">
            <div class="logo" onclick="window.location.href='/'">
                <span class="white">low</span><span class="purple">fun</span>
            </div>
            <div class="nav">
                <span class="welcome-text">welcome, ''' + user + '''</span>
                <a href="/logout">logout</a>''')

        if user == 'riversize':
            html_parts.append('<a href="/admin">admin</a>')

        html_parts.append(
            '''
            </div>
        </div>

        <div class="thread-detail">
            <div class="thread-title">''' + self.escape_html(thread['title']) +
            '''</div>
            <div class="thread-meta">
                by ''' + thread['author'] +
            (' <span class="user-badge">admin</span>' if thread['author'] ==
             'riversize' else '') + ''' • ''' + time.strftime(
                 '%Y-%m-%d %H:%M', time.localtime(thread['timestamp'])) + '''
                ''' +
            ('<form method="post" action="/admin/delete_thread" style="display: inline;"><input type="hidden" name="thread_id" value="'
             + str(thread["id"]) +
             '"><button type="submit" class="delete-btn">delete thread</button></form>'
             if user == 'riversize' else '') + '''
            </div>
            <div class="thread-content">''' +
            self.escape_html(thread['content']).replace(chr(10), '<br>') +
            '''</div>
        </div>

        <div class="add-comment">
            <form method="post" action="/comment">
                <input type="hidden" name="thread_id" value="''' +
            str(thread['id']) + '''">
                <textarea name="content" placeholder="write a comment..." required></textarea>
                <button type="submit">post comment</button>
            </form>
        </div>

        <div class="comments-section">
            <h3 style="color: #8b5cf6; margin-bottom: 20px;">comments (''' +
            str(len(comments)) + ''')</h3>''')

        if comments:
            for comment in comments:
                delete_button = ''
                if user == 'riversize':
                    delete_button = '<form method="post" action="/admin/delete_comment" style="display: inline;"><input type="hidden" name="comment_id" value="' + str(
                        comment["id"]
                    ) + '"><input type="hidden" name="thread_id" value="' + str(
                        thread["id"]
                    ) + '"><button type="submit" class="delete-btn">delete</button></form>'

                admin_badge = ' <span class="user-badge">admin</span>' if comment[
                    'author'] == 'riversize' else ''

                html_parts.append(
                    '''
            <div class="comment">
                <div class="comment-meta">
                    by ''' + comment['author'] + admin_badge + ''' • ''' +
                    time.strftime('%Y-%m-%d %H:%M',
                                  time.localtime(comment['timestamp'])) + '''
                    ''' + delete_button + '''
                </div>
                <div class="comment-content">''' +
                    self.escape_html(comment['content']).replace(
                        chr(10), '<br>') + '''</div>
            </div>''')
        else:
            html_parts.append('''
            <div class="comment">
                <div class="comment-content" style="text-align: center; color: #64748b; padding: 20px;">
                    no comments yet. be the first to comment.
                </div>
            </div>''')

        html_parts.append('''
        </div>
    </div>
</body>
</html>''')

        self.send_html(''.join(html_parts))

    def serve_admin_page(self):
        user = self.get_current_user()
        if user != 'riversize':
            self.redirect('/login?admin=true')
            return

        invites_count = len(data['invites'])
        invites_html = "".join('<div class="invite-code">' + invite + '</div>'
                               for invite in data["invites"])

        self.send_html('''
<!DOCTYPE html>
<html>
<head>
    <title>admin - lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; line-height: 1.4; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 30px; }
        .logo { font-size: 28px; font-weight: 900; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; }
        .stat-card h3 { color: #8b5cf6; margin-bottom: 10px; }
        .invite-section { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 20px; }
        .invite-code { background: #0a0a0a; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; color: #8b5cf6; }
        button { background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 500; }
        button:hover { background: #7c3aed; }
        .back-link { color: #8b5cf6; text-decoration: none; margin-bottom: 20px; display: inline-block; font-weight: 500; }
        .back-link:hover { color: #a78bfa; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← back to forum</a>
        <div class="header">
            <div class="logo" onclick="window.location.href='/'">
                <span class="white">admin</span><span class="purple"> panel</span>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>users</h3>
                <div style="font-size: 24px; font-weight: bold; margin-top: 10px; color: #8b5cf6;">'''
                       + str(len(data['users'])) + '''</div>
            </div>
            <div class="stat-card">
                <h3>threads</h3>
                <div style="font-size: 24px; font-weight: bold; margin-top: 10px; color: #8b5cf6;">'''
                       + str(len(data['threads'])) + '''</div>
            </div>
        </div>

        <div class="invite-section">
            <h3 style="margin-bottom: 15px; color: #8b5cf6;">invite management</h3>
            <form method="post" action="/admin/generate_invite">
                <button type="submit">generate new invite code</button>
            </form>

            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px; color: #c4b5fd;">active invites ('''
                       + str(invites_count) + ''')</h4>
                ''' + invites_html + '''
            </div>
        </div>
    </div>
</body>
</html>''')

    def serve_login_page(self):
        error_message = self.get_error_message()

        self.send_html('''
<!DOCTYPE html>
<html>
<head>
    <title>login - lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 40px; width: 100%; max-width: 400px; }
        .logo { text-align: center; font-size: 32px; font-weight: 900; margin-bottom: 30px; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        input { width: 100%; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; padding: 12px; color: #fff; margin-bottom: 15px; font-family: inherit; }
        input:focus { outline: none; border-color: #8b5cf6; }
        button { width: 100%; background: #8b5cf6; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-family: inherit; margin-top: 10px; font-weight: 500; }
        button:hover { background: #7c3aed; }
        .links { text-align: center; margin-top: 20px; }
        .links a { color: #8b5cf6; text-decoration: none; font-weight: 500; }
        .links a:hover { color: #a78bfa; }
        .error { color: #ef4444; text-align: center; margin-bottom: 15px; padding: 10px; background: #450a0a; border: 1px solid #7f1d1d; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo" onclick="window.location.href='/'">
            <span class="white">low</span><span class="purple">fun</span>
        </div>
        ''' + ('<div class="error">' + error_message +
               '</div>' if error_message else '') + '''
        <form method="post" action="/login">
            <input type="text" name="username" placeholder="username" required>
            <input type="password" name="password" placeholder="password" required>
            <button type="submit">login</button>
        </form>
        <div class="links">
            <a href="/register">need an account? register</a>
        </div>
    </div>
</body>
</html>''')

    def serve_register_page(self):
        error_message = self.get_error_message()

        self.send_html('''
<!DOCTYPE html>
<html>
<head>
    <title>register - lowfun</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .register-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 40px; width: 100%; max-width: 400px; }
        .logo { text-align: center; font-size: 32px; font-weight: 900; margin-bottom: 30px; cursor: pointer; }
        .logo .white { color: #ffffff; }
        .logo .purple { color: #8b5cf6; }
        input { width: 100%; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; padding: 12px; color: #fff; margin-bottom: 15px; font-family: inherit; }
        input:focus { outline: none; border-color: #8b5cf6; }
        button { width: 100%; background: #8b5cf6; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-family: inherit; margin-top: 10px; font-weight: 500; }
        button:hover { background: #7c3aed; }
        .links { text-align: center; margin-top: 20px; }
        .links a { color: #8b5cf6; text-decoration: none; font-weight: 500; }
        .links a:hover { color: #a78bfa; }
        .error { color: #ef4444; text-align: center; margin-bottom: 15px; padding: 10px; background: #450a0a; border: 1px solid #7f1d1d; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="register-box">
        <div class="logo" onclick="window.location.href='/'">
            <span class="white">low</span><span class="purple">fun</span>
        </div>
        ''' + ('<div class="error">' + error_message +
               '</div>' if error_message else '') + '''
        <form method="post" action="/register">
            <input type="text" name="username" placeholder="username" required>
            <input type="password" name="password" placeholder="password" required>
            <input type="text" name="invite_code" placeholder="invite code" required>
            <button type="submit">register</button>
        </form>
        <div class="links">
            <a href="/login">already have an account? login</a>
        </div>
    </div>
</body>
</html>''')

    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def handle_login(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]

        if username == 'riversize' and password == CONFIG['admin_password']:
            session_id = secrets.token_hex(16)
            data['sessions'][session_id] = 'riversize'
            self.redirect('/')
        elif username in data['users']:
            if data['users'][username] == self.hash_password(password):
                session_id = secrets.token_hex(16)
                data['sessions'][session_id] = username
                self.redirect('/')
            else:
                self.redirect('/login?error=invalid_password')
        else:
            self.redirect('/login?error=user_not_found')

    def handle_register(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        invite_code = params.get('invite_code', [''])[0]

        if username in data['users']:
            self.redirect('/register?error=user_exists')
            return

        if invite_code not in data['invites']:
            self.redirect('/register?error=invalid_invite')
            return

        data['users'][username] = self.hash_password(password)
        session_id = secrets.token_hex(16)
        data['sessions'][session_id] = username
        data['invites'].remove(invite_code)
        self.redirect('/')

    def handle_post(self):
        user = self.get_current_user()
        if not user:
            self.redirect('/login')
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        title = params.get('title', [''])[0]
        content = params.get('content', [''])[0]

        if title and content:
            thread = {
                'id': len(data['threads']),
                'title': title,
                'content': content,
                'author': user,
                'timestamp': time.time()
            }
            data['threads'].append(thread)

        self.redirect('/')

    def handle_comment(self):
        user = self.get_current_user()
        if not user:
            self.redirect('/login')
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        thread_id = int(params.get('thread_id', ['0'])[0])
        content = params.get('content', [''])[0]

        if content:
            if thread_id not in data['comments']:
                data['comments'][thread_id] = []

            comment = {
                'id': len(data['comments'][thread_id]),
                'thread_id': thread_id,
                'content': content,
                'author': user,
                'timestamp': time.time()
            }
            data['comments'][thread_id].append(comment)

        self.redirect('/thread/' + str(thread_id))

    def handle_logout(self):
        session_id = self.get_cookie('session_id')
        if session_id in data['sessions']:
            del data['sessions'][session_id]
        self.redirect('/')

    def generate_invite(self):
        user = self.get_current_user()
        if user != 'riversize':
            self.send_error(403)
            return

        chars = string.ascii_lowercase + string.digits
        invite_code = ''.join(random.choice(chars) for _ in range(10))
        data['invites'].append(invite_code)
        self.redirect('/admin')

    def delete_thread(self):
        user = self.get_current_user()
        if user != 'riversize':
            self.send_error(403)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        thread_id = int(params.get('thread_id', ['0'])[0])
        data['threads'] = [t for t in data['threads'] if t['id'] != thread_id]

        if thread_id in data['comments']:
            del data['comments'][thread_id]

        self.redirect('/')

    def delete_comment(self):
        user = self.get_current_user()
        if user != 'riversize':
            self.send_error(403)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urlparse.parse_qs(post_data)

        thread_id = int(params.get('thread_id', ['0'])[0])
        comment_id = int(params.get('comment_id', ['0'])[0])

        if thread_id in data['comments']:
            data['comments'][thread_id] = [
                c for c in data['comments'][thread_id] if c['id'] != comment_id
            ]

        self.redirect('/thread/' + str(thread_id))

    def redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def escape_html(self, text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace(
            '>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')


def main():
    server = HTTPServer((CONFIG['host'], CONFIG['port']), LowFunForum)
    print(
        f"🚀 lowfun forum running on http://{CONFIG['host']}:{CONFIG['port']}")
    print("🔑 admin login: riversize / hvk2osjm")
    print("🎟️  first invite code: welcome1")
    server.serve_forever()


if __name__ == '__main__':
    main()
