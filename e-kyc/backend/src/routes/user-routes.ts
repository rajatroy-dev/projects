import {Router} from 'express';
import UserController from '../controllers/user-controller';

// eslint-disable-next-line new-cap
const routes = Router();

routes.get('/users/:username', UserController.getNominalUserInfo);

export default routes;
