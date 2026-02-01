"""Entry point for the CLI application"""

def main():
    """Main Entry Point"""
    from conviertlo.app import ConviertloApp

    app = ConviertloApp()
    app.run()

if __name__ == "__main__":
    main()
