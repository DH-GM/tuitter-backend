#!/usr/bin/env python3
import sys, time, json, random, string
from datetime import datetime, timezone
import httpx

# --------- Config ----------
BASE_URL = "https://voqbyhcnqe.execute-api.us-east-2.amazonaws.com"  # API Gateway URL
TIMEOUT = 10.0
RETRIES = 5
DELAY = 0.8
TEST_JWT = "<TEST_JWT_HERE>"


def rnd_suffix():
    return f"{int(time.time() * 1000)}{random.randint(1000, 9999)}"


def assert_true(cond, msg, details=None):
    if not cond:
        if details is not None:
            print(details)
        print(f"❌ {msg}")
        sys.exit(1)
    print(f"✅ {msg}")


def req(method, path, *, params=None, json_body=None, authenticated=False):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if authenticated:
        headers["Authorization"] = f"Bearer {TEST_JWT}"

    for i in range(RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=headers,
                )
                resp.raise_for_status()
                # Some endpoints return plain dict/array; return parsed JSON when possible
                try:
                    return resp.json()
                except Exception:
                    return resp.text
        except Exception as e:
            if i == RETRIES - 1:
                raise
            time.sleep(DELAY)
    return None  # unreachable


def main():
    print("=== H E A L T H ===")
    health = req("GET", "/health")
    assert_true(
        health.get("status") == "ok" and health.get("service") == "social.vim API",
        "Health check OK",
    )

    print("=== U S E R S  &  S E T T I N G S ===")
    suf = rnd_suffix()
    user_a = f"tester_{suf}"
    user_b = f"peer_{suf}"

    ua = req("GET", "/me", params={"handle": user_a}, authenticated=True)
    assert_true(ua.get("username") == user_a, f"Created/loaded USER_A={user_a}")

    ub = req("GET", "/me", params={"handle": user_b}, authenticated=True)
    assert_true(ub.get("username") == user_b, f"Created/loaded USER_B={user_b}")

    settings_a = req("GET", "/settings", params={"handle": user_a}, authenticated=True)
    assert_true(settings_a.get("username") == user_a, "Got settings (A)")

    upd = req(
        "PUT",
        "/settings",
        params={"handle": user_a},
        json_body={
            "display_name": "Test A",
            "bio": "Bio A",
            "email_notifications": False,
            "show_online_status": True,
            "private_account": False,
        },
        authenticated=True,
    )
    assert_true(upd.get("success") is True, "Updated settings (A)")

    settings_a2 = req("GET", "/settings", params={"handle": user_a}, authenticated=True)
    assert_true(
        settings_a2.get("display_name") == "Test A"
        and settings_a2.get("bio") == "Bio A"
        and settings_a2.get("email_notifications") is False,
        "Verified settings update (A)",
    )

    print("=== P O S T S  (Create/Read/Like/Repost/Comment) ===")
    post_content = f"Hello from {user_a} at {datetime.now(timezone.utc).isoformat()}"
    post = req(
        "POST",
        "/posts",
        params={"handle": user_a},
        json_body={"content": post_content},
        authenticated=True,
    )
    post_id = post.get("id")
    assert_true(bool(post_id), f"Created post (id={post_id})")

    tl = req(
        "GET", "/timeline", params={"handle": user_a, "limit": 10}, authenticated=True
    )
    assert_true(isinstance(tl, list), "Timeline returns array")
    assert_true(
        any(p.get("id") == post_id for p in tl), "Timeline contains created post"
    )

    like1 = req(
        "POST", f"/posts/{post_id}/like", params={"handle": user_b}, authenticated=True
    )
    assert_true(like1.get("success") is True, "USER_B liked post")
    like2 = req(
        "POST", f"/posts/{post_id}/like", params={"handle": user_b}, authenticated=True
    )
    assert_true(like2.get("success") is True, "USER_B unliked post (toggle)")

    rp1 = req(
        "POST",
        f"/posts/{post_id}/repost",
        params={"handle": user_b},
        authenticated=True,
    )
    assert_true(rp1.get("success") is True, "USER_B reposted post")
    rp2 = req(
        "POST",
        f"/posts/{post_id}/repost",
        params={"handle": user_b},
        authenticated=True,
    )
    assert_true(rp2.get("success") is True, "USER_B un-reposted (toggle)")

    comment_text = f"Nice post from {user_b}!"
    addc = req(
        "POST",
        f"/posts/{post_id}/comments",
        params={"handle": user_b},
        json_body={"text": comment_text},
        authenticated=True,
    )
    assert_true(addc.get("text") == comment_text, "Added comment")

    comments = req("GET", f"/posts/{post_id}/comments", authenticated=True)
    assert_true(
        any(c.get("text") == comment_text for c in comments),
        "Listed comments includes new one",
    )

    print("=== D I S C O V E R  (R) ===")
    disc = req(
        "GET", "/discover", params={"handle": user_a, "limit": 10}, authenticated=True
    )
    assert_true(isinstance(disc, list), "Discover returns array")

    print("=== C O N V E R S A T I O N S  &  M E S S A G E S ===")
    dm = req(
        "POST",
        "/dm",
        json_body={"user_a_handle": user_a, "user_b_handle": user_b},
        authenticated=True,
    )
    conv_id = dm.get("id")
    assert_true(bool(conv_id), f"Created/loaded DM (conversation_id={conv_id})")

    # Send A -> B
    resp_a = req(
        "POST",
        f"/conversations/{conv_id}/messages",
        json_body={"sender_handle": user_a, "content": "Hi from A"},
        authenticated=True,
    )
    # Response schema in your server does NOT include conversation_id; validate by content
    assert_true(resp_a.get("content") == "Hi from A", "A send message")

    # Send B -> A
    resp_b = req(
        "POST",
        f"/conversations/{conv_id}/messages",
        json_body={"sender_handle": user_b, "content": "Hello A, this is B"},
        authenticated=True,
    )
    assert_true(resp_b.get("content") == "Hello A, this is B", "B send message")

    # List & verify both texts
    msgs = req("GET", f"/conversations/{conv_id}/messages", authenticated=True)
    assert_true(isinstance(msgs, list) and len(msgs) >= 2, "Listed DM messages")
    contents = [m.get("content") for m in msgs]
    assert_true(
        "Hi from A" in contents and "Hello A, this is B" in contents,
        "Both message texts present",
    )

    print("=== N O T I F I C A T I O N S  (R/U) ===")
    notifs_a_unread = req(
        "GET",
        "/notifications",
        params={"handle": user_a, "unread": True},
        authenticated=True,
    )
    assert_true(isinstance(notifs_a_unread, list), "Notifications array (A)")
    if notifs_a_unread:
        first_id = notifs_a_unread[0].get("id")
        mr = req("POST", f"/notifications/{first_id}/read", authenticated=True)
        assert_true(mr.get("success") is True, "Marked one notification read (A)")

    notifs_b_unread = req(
        "GET",
        "/notifications",
        params={"handle": user_b, "unread": True},
        authenticated=True,
    )
    assert_true(isinstance(notifs_b_unread, list), "Notifications array (B)")
    if notifs_b_unread:
        first_id_b = notifs_b_unread[0].get("id")
        mr2 = req("POST", f"/notifications/{first_id_b}/read", authenticated=True)
        assert_true(mr2.get("success") is True, "Marked one notification read (B)")

    print("=== R O O T  &  D O C S ===")
    root = req("GET", "/")
    assert_true(
        root.get("service") == "Social.vim API" and root.get("version") == "1.0.0",
        "Root endpoint OK",
    )

    print("=== A U T H  (JWT) ===")

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {TEST_JWT}"}
            )
            resp.raise_for_status()
            data = resp.json()
            assert_true("username" in data, "JWT auth returned valid user claims")
            print("   ->", json.dumps(data, indent=2))
    except Exception as e:
        assert_true(False, "JWT auth test failed", details=str(e))

    print("\n🎉 All integration tests passed")
    print(f"  BASE_URL : {BASE_URL}")
    print(f"  USER_A   : {user_a}")
    print(f"  USER_B   : {user_b}")


if __name__ == "__main__":
    main()
