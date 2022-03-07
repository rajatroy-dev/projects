import express, {NextFunction, Request, Response} from 'express';
import HttpError from './models/http-error';
const app = express();
const port = 6060;

app.get('/', (req: Request, res: Response) => {
  res.send('Hello World!');
});

// 404. No routes found
app.use((_: Request, __:Response, next) => {
  next(new HttpError('API not found!', 404));
});

// Error
app.use((error: HttpError, _: Request, res: Response, next: NextFunction) => {
  if (res.headersSent) {
    return next(error);
  }

  res.status(error.code || 500);
  res.json({error: error.message || 'An unknown error has occured!'});
});

app.listen(port, () => {
  return console.log(`Express is listening at http://localhost:${port}`);
});
