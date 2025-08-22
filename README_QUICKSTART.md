# RENEC Harvester - Quick Start Guide 🚀

Get the RENEC Harvester up and running in minutes!

## Prerequisites Check ✅

```bash
# Check your environment
node --version      # Need v24+
python3 --version   # Need 3.9+
docker --version    # Need Docker installed
```

## 3-Step Quick Start 🏃‍♂️

### Step 1: Clone & Install
```bash
git clone https://github.com/madfam-io/renec-harvester.git
cd renec-harvester
pip3 install -r requirements.txt
```

### Step 2: Start Services
```bash
docker-compose up -d
```

### Step 3: Launch UI
```bash
./start-ui.sh
```

**That's it!** 🎉 Access the UI at http://localhost:3001

## What You'll See

- **Web Interface**: http://localhost:3001
  - Scraping Controls Tab
  - Monitoring Dashboard
  - Data Explorer

- **API Documentation**: http://localhost:8000/docs

## Quick Test

Test if everything is working:

```bash
# Set Python path
export PYTHONPATH=.

# Run test script
python3 scripts/test_local_setup.py
```

You should see: `7/7 tests passed ✅`

## Common Quick Fixes

### Node.js Error?
```bash
brew uninstall node && brew install node
```

### Port Already in Use?
```bash
docker stop $(docker ps -q)
docker-compose up -d
```

### Can't Find Module 'src'?
```bash
export PYTHONPATH=.
```

## What's Next?

1. **Run your first crawl**:
   ```bash
   PYTHONPATH=. python3 -m scrapy crawl renec -a mode=crawl
   ```

2. **Check the monitoring**:
   - Grafana: http://localhost:3000 (admin/renec_grafana_pass)

3. **Explore the API**:
   - http://localhost:8000/docs

## Need Help?

- 📖 [Full Setup Guide](./docs/SETUP_GUIDE.md)
- 🔧 [Troubleshooting Guide](./docs/TROUBLESHOOTING_GUIDE.md)
- 📚 [Complete Documentation](./docs/)

---

**Happy Harvesting!** 🕷️

*Built with ❤️ for the Mexican tech community*