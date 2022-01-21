import express from 'express';
import HttpError from './models/http-error';
const app = express();
const port = 6060;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

// 404. No routes found
app.use((req, res, next) => {
    next(new HttpError("API not found!", 404));
});

// Error
app.use((error: HttpError, _: express.Request, res: express.Response, next: express.NextFunction) => {
    if (res.headersSent) {
        return next(error);
    }

    res.status(error.code || 500);
    res.json({ error: error.message || "An unknown error has occured!" });
})

app.listen(port, () => {
    return console.log(`Express is listening at http://localhost:${port}`);
});