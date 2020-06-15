import {t} from 'app/locale';

import DialogManager from './dialogManager';

type Props = {
  onSave: NonNullable<DialogManager['props']['onSave']>;
} & DialogManager['props'];

type State = DialogManager['state'];

class Add extends DialogManager<Props, State> {
  getTitle() {
    return t('Add relay');
  }
}

export default Add;
