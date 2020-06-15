import React from 'react';
import omit from 'lodash/omit';
import isEqual from 'lodash/isEqual';

import {t} from 'app/locale';
import {ModalRenderProps} from 'app/actionCreators/modal';

import Form from './form';
import Dialog from './dialog';

type FormProps = React.ComponentProps<typeof Form>;
type Values = FormProps['values'];

type Props = ModalRenderProps & {
  onSave?: (values: Values) => void;
};

type State = {
  values: Values;
  requiredValues: Array<keyof Values>;
  disables: FormProps['disables'];
  errors: FormProps['errors'];
  isFormValid: boolean;
  title: string;
};

class DialogManager<
  P extends Props = Props,
  S extends State = State
> extends React.Component<P, S> {
  state: Readonly<S> = this.getDefaultState();

  componentDidMount() {
    this.handleValidateForm();
  }

  componentDidUpdate(_prevProps: Props, prevState: S) {
    if (!isEqual(prevState.values, this.state.values)) {
      this.handleValidateForm();
    }
  }

  getDefaultState(): Readonly<S> {
    return {
      values: {name: '', publicKey: '', description: ''},
      requiredValues: ['name', 'publicKey'],
      errors: {},
      disables: {},
      isFormValid: false,
      title: this.getTitle(),
    } as Readonly<S>;
  }

  getTitle(): string {
    return '';
  }

  clearError = <F extends keyof Values>(field: F) => {
    this.setState(prevState => ({
      errors: omit(prevState.errors, field),
    }));
  };

  handleChange = <F extends keyof Values>(field: F, value: Values[F]) => {
    this.setState(prevState => ({
      values: {
        ...prevState.values,
        [field]: value,
      },
      errors: omit(prevState.errors, field),
    }));
  };

  handleSave = () => {
    const {onSave, closeModal} = this.props;

    if (onSave) {
      onSave(this.state.values);
    }

    closeModal();
  };

  handleValidateForm = () => {
    const {values, requiredValues} = this.state;
    const isFormValid = requiredValues.every(requiredValue => !!values[requiredValue]);
    this.setState({isFormValid});
  };

  handleValidate = <F extends keyof Values>(field: F) => () => {
    const isFieldValueEmpty = !this.state.values[field];
    const fieldErrorAlreadyExist = this.state.errors[field];

    if (isFieldValueEmpty && fieldErrorAlreadyExist) {
      return;
    }

    if (isFieldValueEmpty && !fieldErrorAlreadyExist) {
      this.setState(prevState => ({
        errors: {
          ...prevState.errors,
          [field]: t('Field Required'),
        },
      }));
      return;
    }

    if (!isFieldValueEmpty && fieldErrorAlreadyExist) {
      this.clearError(field);
    }
  };

  renderBody(): React.ReactElement {
    // Child has to implement this
    throw new Error('Not implemented');
  }

  render() {
    const {values, errors, title, isFormValid, disables} = this.state;

    return (
      <Dialog
        {...this.props}
        title={title}
        onSave={this.handleSave}
        disabled={!isFormValid}
        content={
          <Form
            onChange={this.handleChange}
            onValidate={this.handleValidate}
            errors={errors}
            values={values}
            disables={disables}
          />
        }
      />
    );
  }
}

export default DialogManager;
