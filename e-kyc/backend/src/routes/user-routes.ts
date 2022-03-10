import { Router } from 'express';
import * as UserController from '../controllers/user-controller';

const routes = Router();

routes.get('/users/:username', UserController.getNominalUserInfo);

export default routes;
