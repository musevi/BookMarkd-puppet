# BookMarkd

“This fork includes a Puppet control under /puppet that can provision a fresh Debian host with Docker + deploy BookMarkd via docker-compose.”

BookMarkd is an all-in-one book enjoyer's website. This app is much like Letterboxd but for books. Rate books, share books with friends, receive book recommendations, join online book clubs, or set personal reading goals are some of BookMarkd's features.

## Wiki

Wiki for this project is maintained in the class wiki repo here: [Wiki Repo](https://github.com/cs428TAs/f2025/wiki/Incentive-Book-Club)

## Project Structure

```
BookMarkd/
├── backend/          # Flask REST API
├── frontend/         # React application
└── README.md         # This file
```

## Tech Stack

- **Frontend**: React
- **Backend**: Flask (Python)
- **Database**: MySQL/RDS

## Quick Start

### Using Docker Compose (Easiest)

```bash
docker-compose up
```

This will start:

- MySQL database on port 3306
- Flask backend on port 5001
- React frontend on port 3000


## Database Configuration

The application uses MySQL. Update the `DATABASE_URL` in `backend/.env`:

```
DATABASE_URL=mysql://username:password@host:port/database
```

## Development

- Backend runs on port 5001
- Frontend runs on port 5173
- CORS is enabled for local development

## Project Features

- 📚 Rate and review books
- 🤖 Receive personalized book recommendations
- 📖 Join online book clubs
- 🎯 Set and track reading goals
- 📊 View reading statistics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details
