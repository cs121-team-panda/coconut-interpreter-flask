import { call, put, takeLatest } from 'redux-saga/effects';

import * as actionTypes from './actionTypes';
import * as actions from './actions';

import * as api from '../../api';

function* runRequest(action) {
  try {
    const payload = yield call(api.run, action.payload);
    yield put(actions.runSuccess(payload));
  } catch (e) {
    yield put(actions.runFailure(e.toString()));
  }
}

export default function* saga() {
  yield takeLatest(actionTypes.RUN_REQUEST, runRequest);
}
