import argparse

from bkmrks import bkmrks, presenter


def main():
    parser = argparse.ArgumentParser(prog="bkmrks")
    parser.add_argument("--version", action="version", version="%(prog)s v0.4.1")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ## render
    render_parser = subparsers.add_parser(
        "render",
        help="✍️   Render your html bookmarks to public folder.",
    )

    ## load
    load_parser = subparsers.add_parser(
        "load",
        help="📚 Load and HTML file/url and create a bookmark page.",
    )

    load_parser.add_argument(
        "url_or_html_file",
        help="HTML file/url to scrape.",
    )

    load_parser.add_argument(
        "-catalog",
        "-c",
        help="Bookmark catalog name.",
        default="index",
    )

    ## add
    add_parser = subparsers.add_parser(
        "add",
        help="✍️   Add a bookmark to catalog.",
    )

    add_parser.add_argument(
        "url",
        help="URL bookmark to add to the catalog.",
    )

    add_parser.add_argument(
        "-catalog",
        "-c",
        help="Bookmark catalog name.",
        default="index",
    )

    add_parser.add_argument(
        "-line",
        "-l",
        help="Line of the catalog to add your bookmark.",
        default="1",
    )

    add_parser.add_argument(
        "-position",
        "-p",
        help="Position in the line of the catalog to add your bookmark.",
        default="0",
    )

    ## rm
    rm_parser = subparsers.add_parser(
        "rm",
        help="❌ Remove a bookmark from catalog.",
    )

    rm_parser.add_argument(
        "-catalog",
        "-c",
        help="Bookmark catalog name.",
    )

    rm_parser.add_argument(
        "-line",
        "-l",
        help="Line of the catalog to remove your bookmark.",
        default="1",
    )

    rm_parser.add_argument(
        "-position",
        "-p",
        help="Position in the line of the catalog to remove your bookmark.",
        default="1",
    )

    ## mv
    mv_parser = subparsers.add_parser(
        "mv",
        help="🔄 Move a bookmark from a catalog to another.",
    )

    mv_parser.add_argument(
        "-from_catalog",
        "-fc",
        help="Bookmark catalog name to move from.",
        default="index",
    )

    mv_parser.add_argument(
        "-from_line",
        "-fl",
        help="Line of the catalog to move from.",
        default="1",
    )

    mv_parser.add_argument(
        "-from_position",
        "-fp",
        help="Position in the line of the catalog to move from.",
        default="1",
    )

    mv_parser.add_argument(
        "-to_catalog",
        "-tc",
        help="Bookmark catalog name to move to.",
        default="index",
    )

    mv_parser.add_argument(
        "-to_line",
        "-tl",
        help="Line of the catalog to move to.",
        default="1",
    )

    mv_parser.add_argument(
        "-to_position",
        "-tp",
        help="Position in the line of the catalog to move to.",
        default="1",
    )

    ## mvl
    mvl_parser = subparsers.add_parser(
        "mvl",
        help="🔄 Move a line from a catalog to another.",
    )

    mvl_parser.add_argument(
        "-from_catalog",
        "-fc",
        help="Line catalog name to move from.",
        default="index",
    )

    mvl_parser.add_argument(
        "-line",
        "-l",
        "-fl",
        help="Line of the catalog to move from.",
        default="1",
    )

    mvl_parser.add_argument(
        "-to_catalog",
        "-tc",
        help="Catalog name to move to. (default is the same of `-from_catalog`)",
        default=None,
    )

    mvl_parser.add_argument(
        "-new_alias",
        "-a",
        "-na",
        "-tl",
        help="New alias to assume in the catalog.",
        default=None,
    )

    args = parser.parse_args()
    if args.command == "render":
        presenter.render()

    if args.command == "load":
        bkmrks.html2catalog(html_file_name=args.url_or_html_file, catalog=args.catalog)
        presenter.render()

    if args.command == "add":
        bkmrks.add_url(
            url=str(args.url),
            catalog=str(args.catalog),
            line_index=args.line,
            item_index=int(args.position),
        )
        presenter.render()

    if args.command == "rm":
        bkmrks.remove_url(
            catalog=str(args.catalog),
            line_index=args.line,
            item_index=int(args.position),
        )
        presenter.render()

    if args.command == "mv":
        bkmrks.move_url(
            from_catalog=args.from_catalog,
            from_line_index=args.from_line,
            from_item_index=args.from_position,
            to_catalog=args.to_catalog,
            to_line_index=args.to_line,
            to_item_index=args.to_position,
        )
        presenter.render()

    if args.command == "mvl":
        bkmrks.move_line(
            from_catalog=args.from_catalog,
            from_line_index=args.line,
            to_catalog=args.to_catalog,
            new_line_alias=args.new_alias,
        )
        presenter.render()

    return


if __name__ == "__main__":
    main()
