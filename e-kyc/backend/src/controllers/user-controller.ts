import { NextFunction, Request, Response } from 'express';
import { NominalUserInfo } from '../types/nominal-user';

/**
 * @param {Request} req Express request.
 * @param {Response} res Express response.
 * @param {NextFunction} _next Express NextFunction.
 * @return {void} void.
 */
export const getNominalUserInfo = (req: Request, res: Response, next: NextFunction): void => {
  const user: NominalUserInfo = {
    name: 'Abc',
    username: req.params.username,
  };
  res.json({ user });
};
