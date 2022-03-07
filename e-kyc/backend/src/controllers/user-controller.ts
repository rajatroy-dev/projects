import {NextFunction, Request, Response} from 'express';
import {NominalUser} from '../interfaces/nominal-user';

/**
 * Controller for user routes.
 */
export default class UserController {
  /**
       * @param {Request} req Express request.
       * @param {Response} res Express response.
       * @param {NextFunction} next Express NextFunction.
       * @return {void} void.
       */
  static getNominalUserInfo(req: Request, res: Response,
      next: NextFunction): void {
    const user: NominalUser = {
      name: 'Abc',
      username: req.params.username,
    };
    res.json({user});
  }
}
