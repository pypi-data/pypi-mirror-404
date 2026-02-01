from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .api import APIError, MoltbookClient
from .config import DEFAULT_CONFIG_PATH, load_credentials, save_credentials


def _load_api_key(args: argparse.Namespace) -> str | None:
    if args.api_key:
        return args.api_key
    env_key = os.environ.get("MOLTBOOK_API_KEY")
    if env_key:
        return env_key
    creds = load_credentials(Path(args.config))
    return creds.get("api_key")


def _client(args: argparse.Namespace, *, require_key: bool = True) -> MoltbookClient:
    api_key = _load_api_key(args)
    if require_key and not api_key:
        raise SystemExit("Missing API key. Use --api-key, MOLTBOOK_API_KEY, or auth set.")
    base_url = args.base_url.rstrip("/")
    return MoltbookClient(api_key, base_url, timeout=args.timeout)


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=True))


def _print_kv(label: str, value: Any) -> None:
    print(f"{label}: {value}")


def _print_posts(posts: list[dict[str, Any]]) -> None:
    for post in posts:
        title = post.get("title") or "(no title)"
        post_id = post.get("id")
        submolt = post.get("submolt", {}).get("name") if isinstance(post.get("submolt"), dict) else post.get("submolt")
        author = post.get("author", {}).get("name") if isinstance(post.get("author"), dict) else post.get("author")
        created = post.get("created_at")
        upvotes = post.get("upvotes")
        downvotes = post.get("downvotes")
        print(f"- {post_id} | {title}")
        print(f"  submolt={submolt} author={author} up={upvotes} down={downvotes} created={created}")


def _print_comments(comments: list[dict[str, Any]]) -> None:
    for comment in comments:
        comment_id = comment.get("id")
        author = comment.get("author", {}).get("name") if isinstance(comment.get("author"), dict) else comment.get("author")
        upvotes = comment.get("upvotes")
        created = comment.get("created_at")
        content = comment.get("content", "")
        snippet = content[:120].replace("\n", " ")
        print(f"- {comment_id} | {snippet}")
        print(f"  author={author} up={upvotes} created={created}")


def _print_submolts(submolts: list[dict[str, Any]]) -> None:
    for submolt in submolts:
        name = submolt.get("name")
        display = submolt.get("display_name")
        description = submolt.get("description", "")
        snippet = description[:120].replace("\n", " ")
        print(f"- {name} | {display}")
        print(f"  {snippet}")


def cmd_register(args: argparse.Namespace) -> None:
    client = _client(args, require_key=False)
    payload = {"name": args.name, "description": args.description}
    response = client.request("POST", "/agents/register", json_body=payload)
    if args.json:
        _print_json(response)
        return
    agent = response.get("agent", {})
    _print_kv("api_key", agent.get("api_key"))
    _print_kv("claim_url", agent.get("claim_url"))
    _print_kv("verification_code", agent.get("verification_code"))
    if args.save:
        save_credentials(
            Path(args.config),
            {"api_key": agent.get("api_key"), "agent_name": args.name},
        )
        print("Saved credentials.")


def cmd_status(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", "/agents/status")
    if args.json:
        _print_json(response)
        return
    _print_kv("status", response.get("status"))


def cmd_me(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", "/agents/me")
    if args.json:
        _print_json(response)
        return
    agent = response.get("agent", response)
    _print_kv("name", agent.get("name"))
    _print_kv("description", agent.get("description"))
    _print_kv("karma", agent.get("karma"))
    _print_kv("followers", agent.get("follower_count"))
    _print_kv("following", agent.get("following_count"))
    _print_kv("claimed", agent.get("is_claimed"))


def cmd_profile(args: argparse.Namespace) -> None:
    client = _client(args)
    params = {"name": args.name}
    response = client.request("GET", "/agents/profile", params=params)
    if args.json:
        _print_json(response)
        return
    agent = response.get("agent", {})
    _print_kv("name", agent.get("name"))
    _print_kv("description", agent.get("description"))
    _print_kv("karma", agent.get("karma"))
    _print_kv("followers", agent.get("follower_count"))
    _print_kv("following", agent.get("following_count"))
    owner = agent.get("owner", {})
    if owner:
        _print_kv("owner_x", owner.get("x_handle"))


def cmd_update_profile(args: argparse.Namespace) -> None:
    client = _client(args)
    payload: dict[str, Any] = {}
    if args.description:
        payload["description"] = args.description
    if args.metadata:
        payload["metadata"] = json.loads(args.metadata)
    if not payload:
        raise SystemExit("Nothing to update. Provide --description and/or --metadata.")
    response = client.request("PATCH", "/agents/me", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Profile updated.")


def cmd_posts_list(args: argparse.Namespace) -> None:
    client = _client(args)
    params = {"sort": args.sort, "limit": args.limit}
    if args.submolt:
        response = client.request("GET", f"/submolts/{args.submolt}/feed", params=params)
    else:
        response = client.request("GET", "/posts", params=params)
    if args.json:
        _print_json(response)
        return
    posts = response.get("posts", response.get("data", response))
    if isinstance(posts, list):
        _print_posts(posts)
    else:
        _print_json(response)


def cmd_posts_get(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", f"/posts/{args.post_id}")
    if args.json:
        _print_json(response)
        return
    post = response.get("post", response.get("data", response))
    if isinstance(post, dict):
        _print_posts([post])
    else:
        _print_json(response)


def cmd_posts_create(args: argparse.Namespace) -> None:
    if not args.content and not args.url:
        raise SystemExit("Provide --content or --url.")
    if args.content and args.url:
        raise SystemExit("Provide only one of --content or --url.")
    client = _client(args)
    payload = {"submolt": args.submolt, "title": args.title}
    if args.content:
        payload["content"] = args.content
    if args.url:
        payload["url"] = args.url
    response = client.request("POST", "/posts", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Post created.")


def cmd_posts_delete(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("DELETE", f"/posts/{args.post_id}")
    if args.json:
        _print_json(response)
        return
    print("Post deleted.")


def cmd_comments_list(args: argparse.Namespace) -> None:
    client = _client(args)
    params = {"sort": args.sort}
    response = client.request("GET", f"/posts/{args.post_id}/comments", params=params)
    if args.json:
        _print_json(response)
        return
    comments = response.get("comments", response.get("data", response))
    if isinstance(comments, list):
        _print_comments(comments)
    else:
        _print_json(response)


def cmd_comments_add(args: argparse.Namespace) -> None:
    client = _client(args)
    payload = {"content": args.content}
    if args.parent_id:
        payload["parent_id"] = args.parent_id
    response = client.request("POST", f"/posts/{args.post_id}/comments", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Comment posted.")


def cmd_vote_post(args: argparse.Namespace) -> None:
    client = _client(args)
    action = "upvote" if args.direction == "up" else "downvote"
    response = client.request("POST", f"/posts/{args.post_id}/{action}")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Vote sent."))


def cmd_vote_comment_up(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("POST", f"/comments/{args.comment_id}/upvote")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Upvoted comment."))


def cmd_submolts_list(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", "/submolts")
    if args.json:
        _print_json(response)
        return
    submolts = response.get("submolts", response.get("data", response))
    if isinstance(submolts, list):
        _print_submolts(submolts)
    else:
        _print_json(response)


def cmd_submolts_get(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", f"/submolts/{args.name}")
    if args.json:
        _print_json(response)
        return
    submolt = response.get("submolt", response.get("data", response))
    if isinstance(submolt, dict):
        _print_submolts([submolt])
    else:
        _print_json(response)


def cmd_submolts_create(args: argparse.Namespace) -> None:
    client = _client(args)
    payload = {"name": args.name, "display_name": args.display_name, "description": args.description}
    response = client.request("POST", "/submolts", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Submolt created.")


def cmd_submolts_subscribe(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("POST", f"/submolts/{args.name}/subscribe")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Subscribed."))


def cmd_submolts_unsubscribe(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("DELETE", f"/submolts/{args.name}/subscribe")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Unsubscribed."))


def cmd_submolts_settings(args: argparse.Namespace) -> None:
    client = _client(args)
    payload: dict[str, Any] = {}
    if args.description:
        payload["description"] = args.description
    if args.banner_color:
        payload["banner_color"] = args.banner_color
    if args.theme_color:
        payload["theme_color"] = args.theme_color
    if not payload:
        raise SystemExit("Nothing to update. Provide --description, --banner-color, or --theme-color.")
    response = client.request(
        "PATCH",
        f"/submolts/{args.name}/settings",
        json_body=payload,
    )
    if args.json:
        _print_json(response)
        return
    print("Submolt settings updated.")


def cmd_submolts_upload(args: argparse.Namespace) -> None:
    client = _client(args)
    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    with path.open("rb") as handle:
        files = {"file": (path.name, handle, "application/octet-stream"), "type": (None, args.type)}
        response = client.request(
            "POST",
            f"/submolts/{args.name}/settings",
            files=files,
        )
    if args.json:
        _print_json(response)
        return
    print("Submolt asset uploaded.")


def cmd_submolts_mods_list(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("GET", f"/submolts/{args.name}/moderators")
    if args.json:
        _print_json(response)
        return
    mods = response.get("moderators", response.get("data", response))
    if isinstance(mods, list):
        for mod in mods:
            _print_kv(mod.get("agent_name"), mod.get("role"))
    else:
        _print_json(response)


def cmd_submolts_mods_add(args: argparse.Namespace) -> None:
    client = _client(args)
    payload = {"agent_name": args.agent_name, "role": args.role}
    response = client.request("POST", f"/submolts/{args.name}/moderators", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Moderator added.")


def cmd_submolts_mods_remove(args: argparse.Namespace) -> None:
    client = _client(args)
    payload = {"agent_name": args.agent_name}
    response = client.request("DELETE", f"/submolts/{args.name}/moderators", json_body=payload)
    if args.json:
        _print_json(response)
        return
    print("Moderator removed.")


def cmd_follow(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("POST", f"/agents/{args.name}/follow")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Followed."))


def cmd_unfollow(args: argparse.Namespace) -> None:
    client = _client(args)
    response = client.request("DELETE", f"/agents/{args.name}/follow")
    if args.json:
        _print_json(response)
        return
    print(response.get("message", "Unfollowed."))


def cmd_feed(args: argparse.Namespace) -> None:
    client = _client(args)
    params = {"sort": args.sort, "limit": args.limit}
    response = client.request("GET", "/feed", params=params)
    if args.json:
        _print_json(response)
        return
    posts = response.get("posts", response.get("data", response))
    if isinstance(posts, list):
        _print_posts(posts)
    else:
        _print_json(response)


def cmd_search(args: argparse.Namespace) -> None:
    client = _client(args)
    params = {"q": args.query, "type": args.type, "limit": args.limit}
    response = client.request("GET", "/search", params=params)
    if args.json:
        _print_json(response)
        return
    results = response.get("results", [])
    if isinstance(results, list):
        for item in results:
            item_type = item.get("type")
            title = item.get("title") or "(no title)"
            content = item.get("content", "")
            snippet = content[:120].replace("\n", " ")
            print(f"- {item_type} | {title}")
            print(f"  {snippet}")
    else:
        _print_json(response)


def cmd_auth_set(args: argparse.Namespace) -> None:
    api_key = args.api_key or os.environ.get("MOLTBOOK_API_KEY")
    if not api_key:
        raise SystemExit("Provide --api-key or set MOLTBOOK_API_KEY.")
    data = {"api_key": api_key, "agent_name": args.agent_name}
    save_credentials(Path(args.config), data)
    print("Saved credentials.")


def cmd_auth_show(args: argparse.Namespace) -> None:
    creds = load_credentials(Path(args.config))
    if args.json:
        _print_json(creds)
        return
    _print_kv("api_key", creds.get("api_key"))
    _print_kv("agent_name", creds.get("agent_name"))


def cmd_auth_path(args: argparse.Namespace) -> None:
    if args.json:
        _print_json({"path": str(Path(args.config))})
        return
    print(Path(args.config))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mb",
        description="Moltbook CLI client",
    )
    parser.add_argument("--api-key", help="Moltbook API key")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MOLTBOOK_BASE_URL", "https://www.moltbook.com/api/v1"),
        help="API base URL (must include www)",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to credentials JSON",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="Register a new agent")
    register.add_argument("--name", required=True)
    register.add_argument("--description", required=True)
    save_group = register.add_mutually_exclusive_group()
    save_group.add_argument("--save", action="store_true", help="Save credentials", default=True)
    save_group.add_argument("--no-save", action="store_false", dest="save")
    register.set_defaults(func=cmd_register)

    status = subparsers.add_parser("status", help="Check claim status")
    status.set_defaults(func=cmd_status)

    me = subparsers.add_parser("me", help="Show your profile")
    me.set_defaults(func=cmd_me)

    profile = subparsers.add_parser("profile", help="View another agent profile")
    profile.add_argument("--name", required=True)
    profile.set_defaults(func=cmd_profile)

    update_profile = subparsers.add_parser("update-profile", help="Update your profile")
    update_profile.add_argument("--description")
    update_profile.add_argument("--metadata", help="JSON string")
    update_profile.set_defaults(func=cmd_update_profile)

    posts = subparsers.add_parser("posts", help="Post actions")
    posts_sub = posts.add_subparsers(dest="posts_command", required=True)

    posts_list = posts_sub.add_parser("list", help="List posts")
    posts_list.add_argument("--sort", default="hot")
    posts_list.add_argument("--limit", type=int, default=25)
    posts_list.add_argument("--submolt")
    posts_list.set_defaults(func=cmd_posts_list)

    posts_get = posts_sub.add_parser("get", help="Get a post")
    posts_get.add_argument("post_id")
    posts_get.set_defaults(func=cmd_posts_get)

    posts_create = posts_sub.add_parser("create", help="Create a post")
    posts_create.add_argument("--submolt", required=True)
    posts_create.add_argument("--title", required=True)
    posts_create.add_argument("--content")
    posts_create.add_argument("--url")
    posts_create.set_defaults(func=cmd_posts_create)

    posts_delete = posts_sub.add_parser("delete", help="Delete a post")
    posts_delete.add_argument("post_id")
    posts_delete.set_defaults(func=cmd_posts_delete)

    comments = subparsers.add_parser("comments", help="Comment actions")
    comments_sub = comments.add_subparsers(dest="comments_command", required=True)

    comments_list = comments_sub.add_parser("list", help="List comments on a post")
    comments_list.add_argument("post_id")
    comments_list.add_argument("--sort", default="top")
    comments_list.set_defaults(func=cmd_comments_list)

    comments_add = comments_sub.add_parser("add", help="Add a comment")
    comments_add.add_argument("post_id")
    comments_add.add_argument("--content", required=True)
    comments_add.add_argument("--parent-id")
    comments_add.set_defaults(func=cmd_comments_add)

    vote = subparsers.add_parser("vote", help="Voting actions")
    vote_sub = vote.add_subparsers(dest="vote_command", required=True)

    vote_post = vote_sub.add_parser("post", help="Vote on a post")
    vote_post.add_argument("post_id")
    vote_post.add_argument("--direction", choices=["up", "down"], required=True)
    vote_post.set_defaults(func=cmd_vote_post)

    vote_comment = vote_sub.add_parser("comment", help="Upvote a comment")
    vote_comment.add_argument("comment_id")
    vote_comment.set_defaults(func=cmd_vote_comment_up)

    submolts = subparsers.add_parser("submolts", help="Submolt actions")
    submolts_sub = submolts.add_subparsers(dest="submolts_command", required=True)

    submolts_list = submolts_sub.add_parser("list", help="List submolts")
    submolts_list.set_defaults(func=cmd_submolts_list)

    submolts_get = submolts_sub.add_parser("get", help="Get submolt info")
    submolts_get.add_argument("name")
    submolts_get.set_defaults(func=cmd_submolts_get)

    submolts_create = submolts_sub.add_parser("create", help="Create a submolt")
    submolts_create.add_argument("--name", required=True)
    submolts_create.add_argument("--display-name", required=True)
    submolts_create.add_argument("--description", required=True)
    submolts_create.set_defaults(func=cmd_submolts_create)

    submolts_subscribe = submolts_sub.add_parser("subscribe", help="Subscribe to a submolt")
    submolts_subscribe.add_argument("name")
    submolts_subscribe.set_defaults(func=cmd_submolts_subscribe)

    submolts_unsubscribe = submolts_sub.add_parser("unsubscribe", help="Unsubscribe from a submolt")
    submolts_unsubscribe.add_argument("name")
    submolts_unsubscribe.set_defaults(func=cmd_submolts_unsubscribe)

    submolts_settings = submolts_sub.add_parser("settings", help="Update submolt settings")
    submolts_settings.add_argument("name")
    submolts_settings.add_argument("--description")
    submolts_settings.add_argument("--banner-color")
    submolts_settings.add_argument("--theme-color")
    submolts_settings.set_defaults(func=cmd_submolts_settings)

    submolts_upload = submolts_sub.add_parser("upload", help="Upload submolt avatar or banner")
    submolts_upload.add_argument("name")
    submolts_upload.add_argument("--type", choices=["avatar", "banner"], required=True)
    submolts_upload.add_argument("--file", required=True)
    submolts_upload.set_defaults(func=cmd_submolts_upload)

    submolts_mods = submolts_sub.add_parser("mods", help="Moderator management")
    submolts_mods_sub = submolts_mods.add_subparsers(dest="mods_command", required=True)

    submolts_mods_list = submolts_mods_sub.add_parser("list", help="List moderators")
    submolts_mods_list.add_argument("name")
    submolts_mods_list.set_defaults(func=cmd_submolts_mods_list)

    submolts_mods_add = submolts_mods_sub.add_parser("add", help="Add moderator")
    submolts_mods_add.add_argument("name")
    submolts_mods_add.add_argument("--agent-name", required=True)
    submolts_mods_add.add_argument("--role", default="moderator")
    submolts_mods_add.set_defaults(func=cmd_submolts_mods_add)

    submolts_mods_remove = submolts_mods_sub.add_parser("remove", help="Remove moderator")
    submolts_mods_remove.add_argument("name")
    submolts_mods_remove.add_argument("--agent-name", required=True)
    submolts_mods_remove.set_defaults(func=cmd_submolts_mods_remove)

    follow = subparsers.add_parser("follow", help="Follow an agent")
    follow.add_argument("name")
    follow.set_defaults(func=cmd_follow)

    unfollow = subparsers.add_parser("unfollow", help="Unfollow an agent")
    unfollow.add_argument("name")
    unfollow.set_defaults(func=cmd_unfollow)

    feed = subparsers.add_parser("feed", help="Personalized feed")
    feed.add_argument("--sort", default="hot")
    feed.add_argument("--limit", type=int, default=25)
    feed.set_defaults(func=cmd_feed)

    search = subparsers.add_parser("search", help="Semantic search")
    search.add_argument("--query", required=True)
    search.add_argument("--type", default="all", choices=["posts", "comments", "all"])
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=cmd_search)

    auth = subparsers.add_parser("auth", help="Credential management")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)

    auth_set = auth_sub.add_parser("set", help="Save API key")
    auth_set.add_argument("--api-key")
    auth_set.add_argument("--agent-name")
    auth_set.set_defaults(func=cmd_auth_set)

    auth_show = auth_sub.add_parser("show", help="Show saved credentials")
    auth_show.set_defaults(func=cmd_auth_show)

    auth_path = auth_sub.add_parser("path", help="Show credentials path")
    auth_path.set_defaults(func=cmd_auth_path)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except APIError as exc:
        raise SystemExit(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc


if __name__ == "__main__":
    main()
