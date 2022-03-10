import * as UserController from '../../../src/controllers/user-controller';
import { NextFunction, Request, Response } from 'express';
import { NominalUserInfo } from '../../types/nominal-user';

jest.mock('express');

describe('User Controller', () => {
  it('getNominalUserInfo : should send nominal user json as response', () => {
    const mockReq = {
      params: {
        username: 'abc',
      },
    } as unknown as Request;

    const mockNominalUser: NominalUserInfo = { name: 'Abc', username: mockReq.params.username };
    const json = jest.fn();

    UserController.getNominalUserInfo(mockReq, { json } as unknown as Response, {} as NextFunction);

    expect(json).toBeCalledTimes(1);
    expect(json).toHaveBeenCalledWith({ user: mockNominalUser });
  });
});
